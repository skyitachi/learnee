# learnre

亲子电子项目合集，面向 8 岁左右的孩子。每个项目都配有施工文档、电路图和（可选的）Arduino 代码，全程低压电池供电，适合周末亲子一起动手。

## 项目一览

### 1. 可变电阻调光（最简单的入门）

三个元件就能做：220Ω 电阻 + 旋转电位器 + 一颗 LED。拧旋钮改变回路电阻，灯跟着变亮变暗。用来讲透「电阻 → 电流 → 亮度」这条最基础的因果链。

| 文件 | 说明 |
|---|---|
| [可变电阻调光-施工文档.md](led-dimmer/可变电阻调光-施工文档.md) | 原理、材料清单、接线、分步搭建、常见问题、"为什么拧到后面没反应" |
| [可变电阻调光实物图.html](led-dimmer/可变电阻调光实物图.html) | 面包板实物接线图（元件位置 + 跳线走向，按编号插） |

### 2. 魔法小夜灯（光控 LED 灯）

适合第二课：天黑自动亮、有光自动灭的小夜灯。核心元件只有光敏电阻 + 三极管 + LED，用来讲透「传感器 → 电压 → 开关」这条链路。

| 文件 | 说明 |
|---|---|
| [魔法小夜灯-施工文档.md](magic-night-light/魔法小夜灯-施工文档.md) | 原理、材料清单、接线、分步搭建、故障排查、任务卡 |
| [魔法小夜灯电路图.html](magic-night-light/魔法小夜灯电路图.html) | 电路原理图（2N3904 三极管版） |
| [魔法小夜灯实物图.html](magic-night-light/魔法小夜灯实物图.html) | 面包板实物接线图（元件位置 + 跳线走向，按编号插） |

### 3. 鱼缸小卫士（水质监测与报警器）

淡水鱼缸的水温、水位、漏水、浑浊度监测。分 Arduino 版和纯面包板版两个变体。

| 文件 | 说明 |
|---|---|
| [鱼缸小卫士-施工文档.md](fish-guard/鱼缸小卫士-施工文档.md) | Arduino 版完整文档（DS18B20 + OLED + 报警 + 串口日志） |
| [fish_guard.ino](fish-guard/arduino/fish_guard/fish_guard.ino) | 鱼缸主程序 |
| [turbidity_test.ino](fish-guard/arduino/turbidity_test/turbidity_test.ino) | 浑浊度光学方案独立测试程序 |
| [鱼缸小卫士-纯面包板浑浊度.md](fish-guard/鱼缸小卫士-纯面包板浑浊度.md) | 不用 Arduino 的浑浊度阈值报警版 |
| [浑浊度电路图.html](fish-guard/浑浊度电路图.html) | LM393 浑浊度检测电路图 |

## 目录结构

```
learnee/
├── README.md
├── tools/                          # 面包板实物图生成器
│   └── breadboard_mockup.py        # 用法：python3 tools/breadboard_mockup.py [night|dimmer] [out.html]
├── led-dimmer/                     # 可变电阻调光（电位器 + LED）
│   ├── 可变电阻调光-施工文档.md
│   └── 可变电阻调光实物图.html
├── magic-night-light/              # 魔法小夜灯（光控 LED 灯）
│   ├── 魔法小夜灯-施工文档.md
│   ├── 魔法小夜灯电路图.html
│   └── 魔法小夜灯实物图.html
└── fish-guard/                     # 鱼缸小卫士（水质监测与报警器）
    ├── 鱼缸小卫士-施工文档.md
    ├── 鱼缸小卫士-纯面包板浑浊度.md
    ├── 浑浊度电路图.html
    └── arduino/
        ├── fish_guard/
        │   └── fish_guard.ino
        └── turbidity_test/
            └── turbidity_test.ino
```

## 安全提示

- 所有项目全程低压电池（4.5V）或 5V 充电宝供电，**不接市电、不用电烙铁**（亲子场景）。
- 只有密封的传感器（如 DS18B20 防水探头、浮球开关）可以入水，其余元件一律在缸外。
- 鱼缸项目中的 pH、氨氮、亚硝酸盐等化学指标仍需用试剂检测，电子设备只负责物理量报警。
- 8 岁以下或幼儿参与时，注意 LED、三极管等小零件的吞咽风险。
