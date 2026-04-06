# Audio Streaming API - Postman Documentation

This document provides `curl` commands for the Audio Streaming API endpoints. You can use these commands in your terminal or import them directly into Postman.

**How to import into Postman:**
1. Open Postman.
2. Click on the **Import** button in the top left.
3. Select **Raw text**.
4. Paste the `curl` command and click **Continue**, then **Import**.

---

## 1. Extract Audio Stream

Extracts the best quality audio stream URL from a given video link (e.g., YouTube).

- **Method:** `POST`
- **URL:** `http://localhost:5000/api/v1/stream`
- **JSON Body:**
  - `yt_url` (required): The link to the video.

### cURL Command

```bash
curl --location --request POST 'http://localhost:5000/api/v1/stream' \
--header 'Content-Type: application/json' \
--data-raw '{
    "yt_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}'
```

### Expected Responses

**200 OK (Success)**
```json
{
  "original_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "stream_url": "https://manifest.googlevideo.com/api/manifest/dash/... (truncated for brevity)",
  "success": true
}
```

**400 Bad Request (Missing `yt_url` parameter)**
```json
{
  "error": "Missing \"yt_url\" parameter in JSON body.",
  "success": false
}
```

**500 Internal Server Error (Invalid URL or extraction failed)**
```json
{
  "error": "Failed to extract audio stream: ...",
  "success": false
}
```

---

## 2. Play Audio Stream Natively (Proxy)

Directly streams the audio bytes in realtime without exposing the raw YouTube URL to your frontend. This successfully bypasses client-side 403 Forbidden errors and supports `Range` requests, allowing your Flutter audio player to natively play and seek through the music.

- **Method:** `GET`
- **URL:** `http://localhost:5000/api/v1/play?yt_url=<YOUTUBE_URL>`
- **Query Parameter:**
  - `yt_url` (required): The link to the video.

### Example for Flutter's AudioPlayer

```dart
// Using just_audio or audioplayers in Flutter
String ytUrl = Uri.encodeComponent("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
String backendProxyUrl = "http://localhost:5000/api/v1/play?yt_url=$ytUrl";

// Simply set this as your audio source and play!
await audioPlayer.setUrl(backendProxyUrl);
await audioPlayer.play();
```

### cURL Command
(Warning: This will print raw binary audio data to terminal)
```bash
curl --location --request GET 'http://localhost:5000/api/v1/play?yt_url=https://www.youtube.com/watch?v=dQw4w9WgXcQ'
```

---

## 3. Health Check

A simple endpoint to verify that the server is running and healthy.

- **Method:** `GET`
- **URL:** `http://localhost:5000/health`

### cURL Command

```bash
curl --location --request GET 'http://localhost:5000/health'
```

### Expected Response

**200 OK (Success)**
```json
{
  "status": "healthy"
}
```
