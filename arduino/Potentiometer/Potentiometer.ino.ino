/*
  AnalogReadSerial

  Reads an analog input on pin 0, prints the result to the Serial Monitor.
  Graphical representation is available using Serial Plotter (Tools > Serial Plotter menu).
  Attach the center pin of a potentiometer to pin A0, and the outside pins to +5V and ground.

  This example code is in the public domain.

  https://www.arduino.cc/en/Tutorial/BuiltInExamples/AnalogReadSerial
*/

#include "HX711.h"

// Define the pins for the first HX711
const int SG_DOUT_PIN_1 = 52;
const int SG_SCK_PIN_1 = 53;
long previousTime = 0;
long currentTime = 0;

HX711 scale1;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  scale1.begin(SG_DOUT_PIN_1, SG_SCK_PIN_1);
}

// the loop routine runs over and over again forever:
void loop() {
  currentTime = millis();  // Update currentTime before calculating deltaTime
  unsigned long deltaTime = currentTime - previousTime;
  previousTime = currentTime;
  // read the input on analog pin 0:
  int potentiometer = analogRead(A0);
  long loadCell = scale1.read();
  // print out the value you read:
  Serial.print(deltaTime);
  Serial.print(" ");
  Serial.print(loadCell);
  Serial.print(" ");
  Serial.println(potentiometer);
  delay(50);  // delay in between reads for stability
}
