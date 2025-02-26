# API Documentation

## Overview
This API provides functionality to manage and update the availability status on a website, post Instagram stories based on status changes, and retrieve the current status and last update time. The API is designed to handle status updates for "Nightline" platforms, allowing the team to easily update information on the website and on Instagram.

## Authentication
All modifying API requests require an API key for authentication. The API key must be provided as a query parameter `api_key`. If the API key is invalid or missing, a `401 Unauthorized` error will be returned.

---

## Endpoints

### 1. **GET /**

#### Description:
Fetches the current system status and the time of the last update.

#### Response:
- **200 OK**: Returns the current status and the last update time in JSON format.
    - Example:
      ```json
      {
        "status": "default",
        "last_update": "Wed, 08 Jan 2025 18:34:01 GMT"
      }
      ```

### 2. **GET /update_status**

#### Description:
This endpoint updates the system status. The `status` parameter is required, and an optional Instagram story can be uploaded if `story=true` is included. The API checks if the status needs to be updated and if a new Instagram story should be posted.

#### Parameters:
- `api_key` (required): The API key for authentication.
- `status` (required): The new status to be set. Accepted values are:
  - `"default"`
  - `"canceled"`
  - `"german"`
  - `"english"`
- `story` (optional): If `"true"`, an Instagram story will be posted along with the status update.

#### Response:
- **200 OK**: If the status was updated successfully.
  - Example:
    ```json
    {
      "result": "success"
    }
    ```
- **400 Bad Request**: If the provided status is not one of the allowed values.
  - Example:
    ```json
    {
      "result": "fail",
      "description": "status error"
    }
    ```
- **401 Unauthorized**: If the API key is invalid or missing.
  - Example:
    ```json
    {
      "result": "fail",
      "description": "API-KEY error"
    }
    ```

#### Example Request:
```yaml
GET /update_status?api_key=YOUR_API_KEY&status=english&story=true
```

### 3. **GET /update_status_graphical**

#### Description:
Renders a graphical status page where the user will be shown a 'processing' message while the status is being updated.

#### Response:
- **200 OK**: A webpage that shows a processing message.
- This is typically used for user-facing status updates with a visual indication of the process.

#### Example Request:
```yaml
GET /update_status_graphical?api_key=YOUR_API_KEY&status=english&story=true
```

---

## Error Handling

The API provides error responses in the following cases:

- **Invalid API Key**:
  - If the API key is missing or invalid:
    ```json
    {
      "result": "fail",
      "description": "API-KEY error"
    }
    ```
  
- **Invalid Status**:
  - If the provided status is not one of the allowed values:
    ```json
    {
      "result": "fail",
      "description": "status error"
    }
    ```

- **Instagram Story Upload Fail**:
  - If an Instagram story fails to upload while updating the status:
    ```json
    {
      "result": "fail",
      "description": "Failed to upload a story. However, the status was updated successfully."
    }
    ```

---

## Notes

- **Status Options**:  
  The status can be one of the following values:
  - `"default"`
  - `"canceled"`
  - `"german"`
  - `"english"`

- **Instagram Story**:  
  If the `story` parameter is set to `"true"`, the system will attempt to post an Instagram story based on the status. If the request attemts to set the same status as the current status and a story has been posted recently (within 6 hours), it will skip posting a new one. Otherwise it will remove the old story and post a new one.

---

## Troubleshooting

- **Invalid API Key**: Ensure that the correct API key is passed in the `api_key` query parameter.
- **Invalid Status**: Only the statuses `"default"`, `"canceled"`, `"german"`, `"english"` and `"chat"` are accepted. Any other status will result in an error.
- **Instagram Post**: If the Instagram story fails to upload, the status will still be updated, but a failure message will be returned with additional details.
    - Uploading an instagram story might fail if no instagram account is configured