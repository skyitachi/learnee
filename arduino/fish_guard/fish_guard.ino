/*
  鱼缸小卫士 —— 淡水鱼缸 Arduino 水质监测与报警器
  硬件：Arduino Nano / DS18B20 / 0.96" I2C OLED / 有源蜂鸣器 /
        浮球开关 / 漏水探针 / LED + 光敏电阻
  供电：5V USB（充电宝或带漏保的适配器）
  注意：只有密封的 DS18B20 和浮球可以入水，其余传感器都在缸外。
*/

#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <EEPROM.h>

// ---------------- 引脚 ----------------
const uint8_t PIN_DS18B20  = 2;
const uint8_t PIN_BUTTON   = 3;
const uint8_t PIN_FLOAT    = 4;
const uint8_t PIN_TURB_LED = 7;
const uint8_t PIN_LEAK_PWR = 8;
const uint8_t PIN_BUZZER   = 9;
const uint8_t PIN_LEAK     = A0;
const uint8_t PIN_LDR      = A1;

// ---------------- 参数 ----------------
const float TEMP_LOW  = 24.0;    // 按鱼种修改
const float TEMP_HIGH = 28.0;
const float TEMP_HYST = 0.3;     // 回差，避免阈值附近闪烁
const float TEMP_OFFSET = 0.0;   // 和玻璃温度计对比后微调
const unsigned long TEMP_CONFIRM_MS = 60000UL;

const int LEAK_THRESHOLD = 300;  // 0-1023，用湿纸巾实测后调整
const unsigned long WATER_CONFIRM_MS = 2000UL;

const bool USE_TURBIDITY = true; // 没装光学头就改成 false
const bool TURB_INVERT = false;  // 散射式改 true
const int TURB_ALARM_PCT = 20;   // 比干净水少 20% 视为浑浊
const unsigned long TURB_CONFIRM_MS = 600000UL; // 持续 10 分钟才报警

const unsigned long MUTE_MS = 600000UL; // 静音 10 分钟

// ---------------- 对象 ----------------
OneWire oneWire(PIN_DS18B20);
DallasTemperature sensors(&oneWire);
Adafruit_SSD1306 display(128, 64, &Wire, -1);

struct Latch { bool active; unsigned long since; };
Latch cold = {false, 0};
Latch hot = {false, 0};
Latch water = {false, 0};
Latch turbid = {false, 0};
Latch sensorFault = {false, 0};

float tempC = NAN;
float tempMin = 99.0;
float tempMax = -99.0;
bool tempValid = false;
unsigned long tempReqAt = 0;

int baseline = 500;      // 干净水的浑浊度信号，存 EEPROM
int turbSignal = 0;
int cloudPct = 0;
int leakValue = 0;
bool floatClosed = false;

unsigned long mutedUntil = 0;
uint8_t page = 0;

unsigned long lastTurb = 0;
unsigned long lastLeak = 0;
unsigned long lastSerial = 0;
unsigned long lastDisplay = 0;

// ---------------- 工具函数 ----------------
int readAvg(uint8_t pin, uint8_t n) {
  long sum = 0;
  for (uint8_t i = 0; i < n; i++) sum += analogRead(pin);
  return sum / n;
}

int measureTurbiditySignal() {
  digitalWrite(PIN_TURB_LED, LOW);
  delay(30);
  int ambient = readAvg(PIN_LDR, 8);
  digitalWrite(PIN_TURB_LED, HIGH);
  delay(60);
  int lit = readAvg(PIN_LDR, 8);
  digitalWrite(PIN_TURB_LED, LOW);
  int s = lit - ambient;
  return (s < 0) ? 0 : s;
}

int readLeak() {
  digitalWrite(PIN_LEAK_PWR, HIGH);
  delay(5);
  int v = readAvg(PIN_LEAK, 4);
  digitalWrite(PIN_LEAK_PWR, LOW);
  return v;
}

void updateLatch(Latch &l, bool cond, unsigned long confirmMs, unsigned long now) {
  if (!cond) {
    l.active = false;
    l.since = 0;
    return;
  }
  if (l.active) return;
  if (l.since == 0) l.since = now;
  if (now - l.since >= confirmMs) l.active = true;
}

void driveBuzzer(unsigned long now) {
  unsigned long period = 0, on = 0;

  // 漏水和传感器故障不受静音影响
  if (water.active) {
    period = 400; on = 200;
  } else if (sensorFault.active) {
    period = 1000; on = 100;
  } else if (now >= mutedUntil) {
    if (cold.active || hot.active) {
      period = 1500; on = 300;
    } else if (turbid.active) {
      period = 5000; on = 100;
    }
  }

  if (period == 0) digitalWrite(PIN_BUZZER, LOW);
  else digitalWrite(PIN_BUZZER, (now % period) < on ? HIGH : LOW);
}

void handleButton(unsigned long now) {
  static bool lastRaw = false;
  static bool stable = false;
  static unsigned long rawChanged = 0;
  static unsigned long pressStart = 0;

  bool raw = (digitalRead(PIN_BUTTON) == LOW);
  if (raw != lastRaw) {
    lastRaw = raw;
    rawChanged = now;
  }
  if (now - rawChanged >= 20 && raw != stable) {
    stable = raw;
    if (stable) {
      pressStart = now;
    } else {
      unsigned long held = now - pressStart;
      if (held >= 1500) {
        if (mutedUntil > now) mutedUntil = 0;
        else mutedUntil = now + MUTE_MS;
      } else if (held >= 50) {
        page = (page + 1) % 3;
      }
    }
  }
}

void drawFish(int x, int y, bool happy) {
  display.drawCircle(x, y, 7, SSD1306_WHITE);
  display.drawTriangle(x + 7, y, x + 13, y - 4, x + 13, y + 4, SSD1306_WHITE);
  display.drawPixel(x - 2, y - 2, SSD1306_WHITE);
  if (happy) display.drawLine(x - 3, y + 2, x + 1, y + 3, SSD1306_WHITE);
  else       display.drawLine(x - 3, y + 4, x + 1, y + 1, SSD1306_WHITE);
}

void drawScreen() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("FISH GUARD");
  if (millis() < mutedUntil) {
    display.setCursor(92, 0);
    display.print("MUTE");
  }

  if (page == 0) {
    display.setTextSize(3);
    display.setCursor(0, 14);
    if (tempValid) {
      display.print(tempC, 1);
      display.print("C");
    } else {
      display.print("--.-");
    }

    display.setTextSize(1);
    display.setCursor(0, 52);
    bool anyBad = water.active || sensorFault.active || cold.active ||
                  hot.active || turbid.active;
    if (water.active)            display.print("WATER ALARM");
    else if (sensorFault.active) display.print("SENSOR ERROR");
    else if (cold.active)        display.print("TOO COLD");
    else if (hot.active)         display.print("TOO HOT");
    else if (turbid.active)      display.print("WATER CLOUDY");
    else                         display.print("ALL OK");

    drawFish(104, 26, !anyBad);

  } else if (page == 1) {
    display.setCursor(0, 12);
    display.print("MIN "); display.print(tempMin, 1);
    display.print(" MAX "); display.println(tempMax, 1);
    display.print("RANGE "); display.print(TEMP_LOW, 1);
    display.print("-"); display.print(TEMP_HIGH, 1); display.println("C");
    display.print("CLOUD "); display.print(cloudPct); display.println("%");
    display.print("WATER "); display.println(water.active ? "ALARM" : "OK");
    display.print("LEAK "); display.print(leakValue);
    display.print(" FLOAT "); display.println(floatClosed ? 1 : 0);
    display.print("TURB "); display.println(turbSignal);

  } else {
    display.setCursor(0, 12);
    display.println("Calibrate baseline:");
    display.println("clean glass, normal");
    display.println("light, hold button");
    display.println("3s while powering on.");
    display.println();
    display.print("Baseline: "); display.println(baseline);
    display.print("Hold 2s: mute");
  }
  display.display();
}

// ---------------- setup ----------------
void setup() {
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_FLOAT, INPUT_PULLUP);
  pinMode(PIN_TURB_LED, OUTPUT);
  pinMode(PIN_LEAK_PWR, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_TURB_LED, LOW);
  digitalWrite(PIN_LEAK_PWR, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  Serial.begin(9600);
  Serial.println(F("sec,tempC,cloudPct,leak,floatClosed,cold,hot,water,turbid"));

  Wire.begin();
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    display.begin(SSD1306_SWITCHCAPVCC, 0x3D); // 部分模块地址是 0x3D
  }
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("FISH GUARD booting");
  display.display();

  sensors.begin();
  sensors.setResolution(11); // 0.125°C，约 375ms
  sensors.setWaitForConversion(false);
  sensors.requestTemperatures();
  tempReqAt = millis();

  EEPROM.get(0, baseline);
  if (baseline < 50 || baseline > 1023) baseline = 500;
  Serial.print(F("baseline="));
  Serial.println(baseline);

  // 上电时按住按键 3 秒：把当前干净水信号存为浑浊度基线
  if (USE_TURBIDITY && digitalRead(PIN_BUTTON) == LOW) {
    display.setCursor(0, 16);
    display.println("Hold for CAL...");
    display.display();

    unsigned long t0 = millis();
    while (digitalRead(PIN_BUTTON) == LOW && millis() - t0 < 3000) delay(10);

    if (digitalRead(PIN_BUTTON) == LOW) {
      int s = 0;
      for (int i = 0; i < 3; i++) s += measureTurbiditySignal();
      s /= 3;
      Serial.print(F("CAL signal="));
      Serial.println(s);

      display.clearDisplay();
      display.setCursor(0, 0);
      if (s > 50) {
        baseline = s;
        EEPROM.put(0, baseline);
        display.println("CAL saved");
      } else {
        display.println("CAL too dark!");
      }
      display.print("Baseline: ");
      display.println(baseline);
      display.display();
      delay(1200);
    }
    while (digitalRead(PIN_BUTTON) == LOW) delay(10);
  }

  // 吞掉上电时残留的按键动作，避免误翻页
  while (digitalRead(PIN_BUTTON) == LOW) delay(10);
  display.clearDisplay();
}

// ---------------- loop ----------------
void loop() {
  unsigned long now = millis();

  handleButton(now);

  // 温度：非阻塞读取
  if (now - tempReqAt >= 500) {
    float t = sensors.getTempCByIndex(0);
    sensors.requestTemperatures();
    tempReqAt = now;

    if (t > -50.0 && t < 80.0) {
      tempC = t + TEMP_OFFSET;
      tempValid = true;
      if (tempC < tempMin) tempMin = tempC;
      if (tempC > tempMax) tempMax = tempC;
    } else {
      tempValid = false;
    }
  }

  // 漏水：每 500ms 通电测一次
  if (now - lastLeak >= 500) {
    lastLeak = now;
    leakValue = readLeak();
  }
  floatClosed = (digitalRead(PIN_FLOAT) == LOW);

  // 浑浊度：每 5 秒测一次
  if (USE_TURBIDITY && now - lastTurb >= 5000) {
    lastTurb = now;
    int s = measureTurbiditySignal();
    if (turbSignal == 0) turbSignal = s;
    else turbSignal = (turbSignal * 3 + s) / 4; // 平滑

    if (baseline > 0) {
      int pct = TURB_INVERT
        ? (turbSignal - baseline) * 100 / baseline
        : (baseline - turbSignal) * 100 / baseline;
      cloudPct = constrain(pct, 0, 100);
    } else {
      cloudPct = 0;
    }
  }

  // 报警逻辑
  bool coldCond = tempValid && (tempC < TEMP_LOW ||
                  (cold.active && tempC < TEMP_LOW + TEMP_HYST));
  bool hotCond  = tempValid && (tempC > TEMP_HIGH ||
                  (hot.active && tempC > TEMP_HIGH - TEMP_HYST));
  updateLatch(cold, coldCond, TEMP_CONFIRM_MS, now);
  updateLatch(hot, hotCond, TEMP_CONFIRM_MS, now);

  bool waterCond = floatClosed || (leakValue > LEAK_THRESHOLD);
  updateLatch(water, waterCond, WATER_CONFIRM_MS, now);

  updateLatch(sensorFault, !tempValid, 60000UL, now);

  bool turbidCond = USE_TURBIDITY && (cloudPct > TURB_ALARM_PCT);
  updateLatch(turbid, turbidCond, TURB_CONFIRM_MS, now);

  driveBuzzer(now);

  if (now - lastDisplay >= 300) {
    lastDisplay = now;
    drawScreen();
  }

  if (now - lastSerial >= 10000) {
    lastSerial = now;
    float logTemp = tempValid ? tempC : -999.0;
    Serial.print(now / 1000); Serial.print(',');
    Serial.print(logTemp, 1); Serial.print(',');
    Serial.print(cloudPct);   Serial.print(',');
    Serial.print(leakValue);  Serial.print(',');
    Serial.print(floatClosed ? 1 : 0); Serial.print(',');
    Serial.print(cold.active); Serial.print(',');
    Serial.print(hot.active);  Serial.print(',');
    Serial.print(water.active); Serial.print(',');
    Serial.println(turbid.active);
  }
}
