#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Arduino_FreeRTOS.h>
#include "semphr.h"

#define I2C_ADDR 0x27
#define LCD_COLS 16
#define LCD_ROWS 2
#define LM35_PIN A0
#define PHOTO_PIN A1
#define LED_PIN 7  
#define LED_PIN_LIGHT 5    
#define BUZZER_PIN 6

SemaphoreHandle_t ledSemaphore;
SemaphoreHandle_t buzzerSemaphore;
LiquidCrystal_I2C lcd(I2C_ADDR, LCD_COLS, LCD_ROWS);
float temperatureC = 0.0;
int lightIntensity = 0;
SemaphoreHandle_t lcdSemaphore;

// Task to read temperature
void TaskReadTemp(void *pvParameters) {
  (void) pvParameters;
  for (;;) {
    // Read temperature from LM35 sensor
    float voltage = analogRead(LM35_PIN) * (5.0 / 1023.0);
    temperatureC = voltage / 0.01;
    
    // Print temperature to Serial Monitor
    Serial.print("Temperature: ");
    Serial.print(temperatureC);
    Serial.println(" C");

    vTaskDelay(pdMS_TO_TICKS(2000));

    // Check if temperature exceeds 29°C
    if (temperatureC > 29) {
      // Trigger LED and buzzer alarm
      if (xSemaphoreTake(ledSemaphore, pdMS_TO_TICKS(100)) == pdTRUE &&
          xSemaphoreTake(buzzerSemaphore, pdMS_TO_TICKS(100)) == pdTRUE) {
        digitalWrite(LED_PIN, HIGH);
        vTaskDelay(pdMS_TO_TICKS(1000));
        digitalWrite(LED_PIN, LOW);
        tone(BUZZER_PIN, 10000);
        xSemaphoreGive(buzzerSemaphore);
        xSemaphoreGive(ledSemaphore);
      }
    } else {
      // Reset LED and buzzer
      if (xSemaphoreTake(ledSemaphore, pdMS_TO_TICKS(100)) == pdTRUE &&
          xSemaphoreTake(buzzerSemaphore, pdMS_TO_TICKS(100)) == pdTRUE) {
        digitalWrite(LED_PIN, LOW);
        noTone(BUZZER_PIN);
        xSemaphoreGive(buzzerSemaphore);
        xSemaphoreGive(ledSemaphore);
      }
    }

    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

// Task to read light intensity
void TaskReadLight(void *pvParameters) {
  (void) pvParameters;
  for (;;) {
    // Read light intensity from photoresistor
    lightIntensity = analogRead(PHOTO_PIN);
    
    // Print light intensity to Serial Monitor
    Serial.print("Light Intensity: ");
    Serial.print(lightIntensity);

    vTaskDelay(pdMS_TO_TICKS(2000));

    // Control LED based on light intensity
    if (lightIntensity < 15) {
      digitalWrite(LED_PIN_LIGHT, HIGH);
      xSemaphoreGive(ledSemaphore);
    } else {
      digitalWrite(LED_PIN_LIGHT, LOW);
      xSemaphoreGive(ledSemaphore);
    }

    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

// Task to display data on LCD
void TaskDisplay(void *pvParameters) {
  (void) pvParameters;

  // Create a counting semaphore with a capacity of 2
  lcdSemaphore = xSemaphoreCreateCounting(2, 2);

  for (;;) {
    if (xSemaphoreTake(lcdSemaphore, pdMS_TO_TICKS(100)) == pdTRUE) {
      // Display temperature on LCD
      lcd.setCursor(0, 0);
      lcd.print("Temp: ");
      lcd.print(temperatureC);
      lcd.print(" C");

      // Display light intensity on LCD
      lcd.setCursor(0, 1);
      lcd.print("Light: ");
      lcd.print(lightIntensity);
      
      xSemaphoreGive(lcdSemaphore);
    }

    vTaskDelay(pdMS_TO_TICKS(1000));

    // Clear LCD display for the next update
    lcd.clear();
  }
}

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  pinMode(LED_PIN, OUTPUT);
  pinMode(LED_PIN_LIGHT, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Create binary semaphores and initialize them
  ledSemaphore = xSemaphoreCreateBinary();
  buzzerSemaphore = xSemaphoreCreateBinary();
  
  if (ledSemaphore != NULL && buzzerSemaphore != NULL) {
    xSemaphoreGive(ledSemaphore);
    xSemaphoreGive(buzzerSemaphore);
  }

  // Create and start FreeRTOS tasks
  xTaskCreate(TaskReadTemp, "Read Temp Task", 128, NULL, 1, NULL);
  xTaskCreate(TaskReadLight, "Read Light Task", 128, NULL, 1, NULL);
  xTaskCreate(TaskDisplay, "Display Task", 128, NULL, 2, NULL);

  vTaskStartScheduler();
}

void loop() {
  // Empty loop since tasks are being used
}
