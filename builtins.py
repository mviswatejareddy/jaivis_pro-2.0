{
  "intents": [
    {
      "tag": "greeting",
      "patterns": ["hi", "hello", "hey jarvis", "good morning", "good evening"],
      "responses": ["Hello. Ready when you are.", "Hi, how can I help you?", "Greetings. What task should I run?"]
    },
    {
      "tag": "time_query",
      "patterns": ["what time is it", "tell me the time", "current time", "jarvis time now"],
      "responses": ["Let me check the current time.", "Here is the current time."]
    },
    {
      "tag": "date_query",
      "patterns": ["what is the date", "today's date", "date today", "which day is it"],
      "responses": ["Checking today's date.", "Here is today's date."]
    },
    {
      "tag": "math_eval",
      "patterns": ["calculate 25 plus 17", "evaluate 9 * 8", "solve 100/4", "compute 7 power 2"],
      "responses": ["I will calculate that.", "Running the expression now."]
    },
    {
      "tag": "system_status",
      "patterns": ["system status", "how are you jarvis", "health check", "are you online"],
      "responses": ["All systems are operational.", "Runtime looks healthy."]
    },
    {
      "tag": "exit",
      "patterns": ["exit", "quit", "stop jarvis", "shutdown assistant"],
      "responses": ["Goodbye.", "Session ended.", "Shutting down now."]
    },
    {
      "tag": "fallback",
      "patterns": ["i need help", "can you assist me", "do something smart", "what can you do"],
      "responses": ["I can answer intents, run calculations, and execute command handlers.", "Ask me about time, date, math, or extend me with new skills."]
    }
  ]
}
