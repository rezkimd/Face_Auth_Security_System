#include <WiFi.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <PubSubClient.h>

#define pinIR  2   //Deklarasi pin sensor pada A0
#define ledPin 4      //Deklarasi pin Led pada A1
#define buzzerPin 16

const char* ssid = "Finally";
const char* password = "bombom357";

const char* mqtt_server = "broker.hivemq.com";  // Example using HiveMQ's public broker
const int mqtt_port = 8884;

WiFiClient espClient;
PubSubClient client(espClient);

const char* mqtt_topic_subscribe = "homeAuth/2106731516/ESP32";
const char* mqtt_topic_publish = "homeAuth/2106731516/cloud";

String dataPayload;
String strTopic;
String strPayload;
char buff[100];

int lcdColumns = 16;
int lcdRows = 2;
LiquidCrystal_I2C lcd(0x27, lcdColumns, lcdRows);

// Task handle
TaskHandle_t InfraTaskHandle;

void InfraRedTrigger(void *parameter) {
  for (;;) {
    int datasensor = digitalRead(pinIR); // Read the digital value from IR sensor
    Serial.print("Data Sensor: ");
    Serial.println(datasensor);
    
    if (datasensor == LOW) { // If the sensor detects something
      lcd.clear();
      Serial.println("Infrared trigger");
      lcd.setCursor(0, 0);
      lcd.print("Deteksi aktif");
      
      // Wait for a notification from Python before resuming the loop
      uint32_t ulNotificationValue;
      BaseType_t xResult = xTaskNotifyWait(0, ULONG_MAX, &ulNotificationValue, portMAX_DELAY);
      
      // Check if notification was received (the task will unblock here)
      if (xResult == pdTRUE && ulNotificationValue == 1) {
        Serial.println("Notif accepted, resuming task...");
      }

      delay(250); // Short delay to stabilize the display
    } 
    
    else {
      lcd.clear();
      // Serial.println("Menunggu respon....");
      lcd.setCursor(0, 0);
      lcd.print("Menunggu respon..");
      delay(250); // Short delay to stabilize the display
    }

    vTaskDelay(1000 / portTICK_PERIOD_MS); // Delay for 1 second (1000ms)
  }
}

void setup_wifi(){
  delay(10);
  Serial.print("Try to connect : ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print("Connecting...\n");
  }

  Serial.print("Connected to : ");
  Serial.println(ssid);
  Serial.print("IP address : ");
  Serial.println(WiFi.localIP());
}

void connect_mqtt() {
  // Loop until connected to MQTT server
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Try to connect (clientID)
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
      // Subscribe to the topic
      client.subscribe(mqtt_topic_subscribe);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  // setup_wifi();

  // connect_mqtt();

  lcd.init();
  lcd.backlight();

  pinMode(pinIR, INPUT);  //Deklarasi pin A0 sebagai input
  pinMode(ledPin, OUTPUT);   //Deklarasi pin A1 sebagai output
  
  // Set the MQTT server and define the callback function
  // client.setServer(mqtt_server, mqtt_port);
  // client.setCallback(callback);

  Serial.println("Module All clear >W<\n");

  //Task InfraRed Sensor
  // Create the sensor task with a stack size of 2048 bytes, priority of 1
  xTaskCreate(
    InfraRedTrigger,          // Function to implement the task
    "Sensor Task",       // Name of the task
    2048,                // Stack size in words
    NULL,                // Task input parameter
    1,                   // Priority of the task
    &InfraTaskHandle    // Task handle to keep track of created task
  );
}

void loop() {
    // Check for incoming serial data from Python
  if (Serial.available() > 0) {
    // Read the incoming message until a newline character is detected
    String receivedData = Serial.readStringUntil('\n');
    receivedData.trim(); // Remove any trailing whitespace

    // Check if the received message matches "Hello, Master"
    if (receivedData == "Hello, Master") {
      // Turn on the LED
      digitalWrite(ledPin, HIGH);
      delay(3000); // Keep the LED on for 3 seconds
      digitalWrite(ledPin, LOW); // Turn off the LED after 3 seconds
    } 
    // Check if the received message matches "it is not you"
    else if (receivedData == "Not recognized") {
      // Turn on the Buzzer
      digitalWrite(buzzerPin, HIGH);
      delay(3000); // Keep the buzzer on for 3 seconds
      digitalWrite(buzzerPin, LOW); // Turn off the buzzer after 3 seconds
    }

    // Display the received message on the LCD
    lcd.setCursor(0, 1);  // Adjust to the correct position for your LCD
    lcd.print(receivedData);
    delay(3000); // Keep the message on the LCD for 3 seconds

    // Notify the InfraTaskHandle (if needed for your task)
    xTaskNotify(InfraTaskHandle, 1, eSetValueWithOverwrite);
    }
    delay(100);
  }
