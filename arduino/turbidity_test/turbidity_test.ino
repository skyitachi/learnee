/*
  浑浊度传感器最小测试
  目的：验证 LED + 光敏电阻的光学方案能否稳定区分清水和浑水，
        通过后再决定是否接入主程序（fish_guard.ino）。
  硬件：Arduino + 红色/红外 LED + 220Ω + 光敏电阻 GL5528 + 10kΩ
  接线（与主程序保持一致，方便迁移）：
        LED 正极 -- 220Ω -- D7，LED 负极 -- GND
        5V -- 光敏电阻 -- A1，A1 -- 10kΩ -- GND
  输出：每秒一行 CSV：样本序号, 环境光, LED亮时读数, 信号(=亮-环境)
        可直接用 Arduino IDE 的“串口绘图器”看曲线。
*/

const uint8_t PIN_TURB_LED = 7;
const uint8_t PIN_LDR      = A1;

const unsigned long SAMPLE_MS = 1000;  // 每秒测一次，想更快改成 500

int readAvg(uint8_t pin, uint8_t n) {
  long sum = 0;
  for (uint8_t i = 0; i < n; i++) sum += analogRead(pin);
  return sum / n;
}

void setup() {
  pinMode(PIN_TURB_LED, OUTPUT);
  digitalWrite(PIN_TURB_LED, LOW);
  Serial.begin(9600);
  Serial.println(F("sample, ambient, lit, signal"));
}

void loop() {
  static unsigned long last = 0;
  if (millis() - last < SAMPLE_MS) return;
  last = millis();

  // 1. 关 LED，测环境光（用来抵消室内灯光干扰）
  digitalWrite(PIN_TURB_LED, LOW);
  delay(30);
  int ambient = readAvg(PIN_LDR, 8);

  // 2. 开 LED，测透射/散射光
  digitalWrite(PIN_TURB_LED, HIGH);
  delay(60);
  int lit = readAvg(PIN_LDR, 8);
  digitalWrite(PIN_TURB_LED, LOW);

  int signal = lit - ambient;
  if (signal < 0) signal = 0;

  Serial.print(millis() / 1000);
  Serial.print(F(", "));
  Serial.print(ambient);
  Serial.print(F(", "));
  Serial.print(lit);
  Serial.print(F(", "));
  Serial.println(signal);
}
