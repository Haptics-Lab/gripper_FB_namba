// 把持力フィードバック//1205
#include <RotaryEncoder.h>
// ロードセル
int loadcell_rec = 127;

// アナログピン34,13 モーター->マイコン エンコーダー用
const int ENCODER_PIN_1 = 32;
const int ENCODER_PIN_2 = 33;
const int ENCODER_PIN_3 = 34;
const int ENCODER_PIN_4 = 35;

// アナログピン25,26 マイコン->モータ モータ制御用
const int DAC_PIN_1 = 26;
const int DAC_PIN_2 = 25;

// ESP32並列処理
volatile int vol1_int = 127;
volatile int vol2_int = 127;
volatile float volt = 127; // Lowpass-fft用
// PID
volatile int newpos1_int = 0;
volatile int newpos2_int = 0;

float pretime = 0;
float preP1 = 0;
float preP2 = 0;
float Kd1 = 0.004; // 発振用ダンパ係数
float Kp2 = 0.05;  // PIDをゆるく
float Kd2 = 0.005;
float dt = 0.005;
float P1;
float P2;
float D1;
float D2;
float a = 0.99; // Lowpass-fft用
RotaryEncoder encoder1(ENCODER_PIN_1, ENCODER_PIN_2, RotaryEncoder::LatchMode::TWO03);
RotaryEncoder encoder2(ENCODER_PIN_3, ENCODER_PIN_4, RotaryEncoder::LatchMode::TWO03);

void IRAM_ATTR ISR()
{
  encoder1.tick();
  encoder2.tick();
}

void subProcess(void *pvParameters)
{ // 並列処理の関数
  while (1)
  {
    newpos1_int = (int)encoder1.getPosition(); // 元々のgetPositionはintで拾う？ → 確認したらlong型でした．実機で動かしてから修正したい．
    newpos2_int = (int)encoder2.getPosition(); // 腹を括って並列処理を削除．動かなかったら戻す．

    if (Serial.available())
    {
      loadcell_rec = Serial.read();
    }
    D1 = (preP1 - newpos1_int) / dt;
    preP1 = newpos1_int;
    P2 = newpos1_int - newpos2_int;
    D2 = (P2 - preP2) / dt;
    preP2 = P2;
    volt = a * volt + (1 - a) * loadcell_rec;
    //    vol1_int = int(volt + Kd1* D1);
    vol1_int = int(loadcell_rec + Kd1 * D1);   // コントロール側は今まで通り反力くる0.004体験
    vol2_int = int(Kp2 * P2 + Kd2 * D2 + 127); // サポート側はスクイーズで反力くる

    if (vol1_int > 255)
    {
      vol1_int = 255;
    }
    else if (vol1_int < 0)
    {
      vol1_int = 0;
    }
    if (vol2_int > 255)
    {
      vol2_int = 255;
    }
    else if (vol2_int < 0)
    {
      vol2_int = 0;
    }
    dacWrite(DAC_PIN_1, vol1_int);
    dacWrite(DAC_PIN_2, vol2_int);
    delay(5);
  }
}

void setup()
{
  pinMode(ENCODER_PIN_1, INPUT_PULLUP);
  pinMode(ENCODER_PIN_2, INPUT_PULLUP);
  pinMode(ENCODER_PIN_3, INPUT_PULLUP);
  pinMode(ENCODER_PIN_4, INPUT_PULLUP);
  pinMode(DAC_PIN_1, OUTPUT);
  pinMode(DAC_PIN_2, OUTPUT);
  Serial.begin(115200);
  Serial.println("SimplePollRotator example for the RotaryEncoder library.");
  attachInterrupt(digitalPinToInterrupt(ENCODER_PIN_1), ISR, CHANGE); // 割り込み処理はできるだけ簡単にINPUTしてないのにできてるのは気持ち悪い、
  attachInterrupt(digitalPinToInterrupt(ENCODER_PIN_2), ISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_PIN_3), ISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENCODER_PIN_4), ISR, CHANGE);
  xTaskCreatePinnedToCore(subProcess, "subProcess", 4096, NULL, 1, NULL, 0); // 並列処理
}

void loop()
{
  Serial.print(-newpos1_int);
  Serial.print(',');
  Serial.print(-newpos2_int);
  Serial.print(',');
  Serial.print(vol1_int);
  Serial.print(',');
  Serial.println(vol2_int);
  delay(5); // 200Hz
}
