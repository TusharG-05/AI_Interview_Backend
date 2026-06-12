# API Documentation

This document details the REST APIs for the application, including endpoint paths, methods, request parameters, request bodies, and response structures along with their data types.

---

## `POST /api/auth/login`

**Summary**: Login

JSON-based login. Sets secure HttpOnly cookie and returns token.

### Request Body
<ul><li><b>email</b>: <code>string</code> (Required)</li><li><b>password</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/auth/token`

**Summary**: Login For Access Token

Standard OAuth2 token endpoint for Swagger UI (Authorize button).

### Request Body
Content-Type: `application/x-www-form-urlencoded`

<ul><li><b>grant_type</b>: <code>string</code> (Optional)</li><li><b>username</b>: <code>string</code> (Required)</li><li><b>password</b>: <code>string</code> (Required)</li><li><b>scope</b>: <code>string</code> (Optional)</li><li><b>client_id</b>: <code>string</code> (Optional)</li><li><b>client_secret</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>token_type</b>: <code>string</code> (Required)</li><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>expires_at</b>: <code>string</code> (Required)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/auth/logout`

**Summary**: Logout

Clears the authentication cookie.

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

---

## `POST /api/auth/register`

**Summary**: Register

Register a new user. 
- First user can register freely (Bootstrap).
- Subsequent users must be registered by an Admin.

### Request Body
<ul><li><b>email</b>: <code>string</code> (Required)</li><li><b>password</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Optional)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>token_type</b>: <code>string</code> (Required)</li><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>expires_at</b>: <code>string</code> (Required)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/auth/signup/candidate`

**Summary**: Candidate Signup

Public signup for candidates.
- Creates a User with role=CANDIDATE.
- Creates an associated UserDetail entry.
- Automatically logs in the user and returns a token.

### Request Body
<ul><li><b>email</b>: <code>string</code> (Required)</li><li><b>password</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/auth/me`

**Summary**: Read Users Me

Get current logged in user details with complete profile information.

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

---

## `PUT /api/auth/fcm-token`

**Summary**: Update Fcm Token

Registers or updates the user's Firebase Cloud Messaging token.
Enables targeted push notifications for browser events.

### Request Body
<ul><li><b>fcm_token</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/status/`

**Summary**: Get System Status

Comprehensive health check for AI services (Isolate by session).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | query | No | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/papers`

**Summary**: List Papers

List all question papers created by the admin.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/papers`

**Summary**: Create Paper

Create a new collection of questions.

### Request Body
<ul><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/upload-doc`

**Summary**: Upload Questions Doc

Upload a document (.pdf, .docx, .txt, .xlsx) to extract questions and add them to a paper.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | query | Yes | `integer` |  |

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>file</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/papers/{paper_id}`

**Summary**: Get Paper

Get details of a specific question paper.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/papers/{paper_id}`

**Summary**: Update Paper

Update a question paper's name or description.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>name</b>: <code>string</code> (Optional)</li><li><b>description</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/papers/{paper_id}`

**Summary**: Delete Paper

Delete a question paper and all its associated questions.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/papers/{paper_id}/questions`

**Summary**: Add Question To Paper

API for manually adding a new interview question to a paper.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/papers/{paper_id}/questions`

**Summary**: List Paper Questions

List all questions belonging to a specific question paper.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/generate-paper`

**Summary**: Generate Paper

Generate a complete question paper using AI.

Accepts an AI prompt (topic/job description), the expected years of experience,
and the number of questions to generate. The LLM produces the questions and
the resulting QuestionPaper is persisted in the database.

### Request Body
<ul><li><b>ai_prompt</b>: <code>string</code> (Required)</li><li><b>years_of_experience</b>: <code>integer</code> (Required)</li><li><b>num_questions</b>: <code>integer</code> (Required)</li><li><b>paper_name</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/generate-coding-paper`

**Summary**: Generate Coding Paper

Generate LeetCode-style coding problems via AI and append them to an
existing CodingQuestionPaper. Each problem is saved as a structured
`CodingQuestions` row (title, problem_statement, examples, constraints,
starter_code) — not a JSON blob.

### Request Body
<ul><li><b>ai_prompt</b>: <code>string</code> (Required)</li><li><b>difficulty_mix</b>: <code>string</code> (Optional)</li><li><b>num_questions</b>: <code>integer</code> (Required)</li><li><b>paper_name</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>created_by</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/questions/{q_id}`

**Summary**: Delete Question

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `q_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/questions/{q_id}`

**Summary**: Get Question

Get details of a specific question.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `q_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/questions/{q_id}`

**Summary**: Update Question

Update specific fields of a question.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `q_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li><li><b>response_type</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/candidates/{user_id}`

**Summary**: Admin Get Candidate Profile

Admin: Get any candidate's profile and details.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>details</b>: <code><ul><li><b>date_of_birth</b>: <code>string</code> (Optional)</li><li><b>gender</b>: <code>string</code> (Optional)</li><li><b>blood_group</b>: <code>string</code> (Optional)</li><li><b>nationality</b>: <code>string</code> (Optional)</li><li><b>religion</b>: <code>string</code> (Optional)</li><li><b>marital_status</b>: <code>string</code> (Optional)</li><li><b>father_name</b>: <code>string</code> (Optional)</li><li><b>mother_name</b>: <code>string</code> (Optional)</li><li><b>guardian_name</b>: <code>string</code> (Optional)</li><li><b>guardian_relation</b>: <code>string</code> (Optional)</li><li><b>phone_number</b>: <code>string</code> (Optional)</li><li><b>alternate_phone</b>: <code>string</code> (Optional)</li><li><b>address_line1</b>: <code>string</code> (Optional)</li><li><b>address_line2</b>: <code>string</code> (Optional)</li><li><b>city</b>: <code>string</code> (Optional)</li><li><b>state</b>: <code>string</code> (Optional)</li><li><b>postal_code</b>: <code>string</code> (Optional)</li><li><b>country</b>: <code>string</code> (Optional)</li><li><b>aadhar_number</b>: <code>string</code> (Optional)</li><li><b>pan_number</b>: <code>string</code> (Optional)</li><li><b>passport_number</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_name</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_phone</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_relation</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>updated_at</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/candidates/{user_id}`

**Summary**: Admin Update Candidate Profile

Admin: Update any candidate's profile and details.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>date_of_birth</b>: <code>string</code> (Optional)</li><li><b>gender</b>: <code>string</code> (Optional)</li><li><b>blood_group</b>: <code>string</code> (Optional)</li><li><b>nationality</b>: <code>string</code> (Optional)</li><li><b>religion</b>: <code>string</code> (Optional)</li><li><b>marital_status</b>: <code>string</code> (Optional)</li><li><b>father_name</b>: <code>string</code> (Optional)</li><li><b>mother_name</b>: <code>string</code> (Optional)</li><li><b>guardian_name</b>: <code>string</code> (Optional)</li><li><b>guardian_relation</b>: <code>string</code> (Optional)</li><li><b>phone_number</b>: <code>string</code> (Optional)</li><li><b>alternate_phone</b>: <code>string</code> (Optional)</li><li><b>address_line1</b>: <code>string</code> (Optional)</li><li><b>address_line2</b>: <code>string</code> (Optional)</li><li><b>city</b>: <code>string</code> (Optional)</li><li><b>state</b>: <code>string</code> (Optional)</li><li><b>postal_code</b>: <code>string</code> (Optional)</li><li><b>country</b>: <code>string</code> (Optional)</li><li><b>aadhar_number</b>: <code>string</code> (Optional)</li><li><b>pan_number</b>: <code>string</code> (Optional)</li><li><b>passport_number</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_name</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_phone</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_relation</b>: <code>string</code> (Optional)</li><li><b>full_name</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>details</b>: <code><ul><li><b>date_of_birth</b>: <code>string</code> (Optional)</li><li><b>gender</b>: <code>string</code> (Optional)</li><li><b>blood_group</b>: <code>string</code> (Optional)</li><li><b>nationality</b>: <code>string</code> (Optional)</li><li><b>religion</b>: <code>string</code> (Optional)</li><li><b>marital_status</b>: <code>string</code> (Optional)</li><li><b>father_name</b>: <code>string</code> (Optional)</li><li><b>mother_name</b>: <code>string</code> (Optional)</li><li><b>guardian_name</b>: <code>string</code> (Optional)</li><li><b>guardian_relation</b>: <code>string</code> (Optional)</li><li><b>phone_number</b>: <code>string</code> (Optional)</li><li><b>alternate_phone</b>: <code>string</code> (Optional)</li><li><b>address_line1</b>: <code>string</code> (Optional)</li><li><b>address_line2</b>: <code>string</code> (Optional)</li><li><b>city</b>: <code>string</code> (Optional)</li><li><b>state</b>: <code>string</code> (Optional)</li><li><b>postal_code</b>: <code>string</code> (Optional)</li><li><b>country</b>: <code>string</code> (Optional)</li><li><b>aadhar_number</b>: <code>string</code> (Optional)</li><li><b>pan_number</b>: <code>string</code> (Optional)</li><li><b>passport_number</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_name</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_phone</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_relation</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>updated_at</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/candidates/{user_id}`

**Summary**: Admin Delete Candidate

Admin: Delete any candidate's account.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/questions`

**Summary**: List All Questions

List all questions across all papers owned by the admin (including global ones).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/interviews/schedule`

**Summary**: Schedule Interview

Schedule a new one-to-one interview and email the link.

### Request Body
<ul><li><b>candidate_id</b>: <code>integer</code> (Required)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>coding_paper_id</b>: <code>integer</code> (Optional)</li><li><b>interview_round</b>: <code>string</code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Required)</li><li><b>duration_minutes</b>: <code>integer</code> (Optional)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>interview</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>interview_round</b>: <code>string</code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Required)</li><li><b>duration_minutes</b>: <code>integer</code> (Required)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Required)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Required)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_path</b>: <code>string</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>coding_paper_id</b>: <code>integer</code> (Optional)</li></ul></code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Required)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>link</b>: <code>string</code> (Required)</li><li><b>scheduled_at</b>: <code>string</code> (Required)</li><li><b>warning</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/interviews`

**Summary**: List Interviews

List interviews created by this admin.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |
| `from_date` | query | No | `string` |  |
| `to_date` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Required)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>schedule_time</b>: <code>string</code> (Required)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>interview_round</b>: <code>string</code> (Optional)</li><li><b>result_status</b>: <code>string</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>proctoring_event</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>tab_switch_count</b>: <code>integer</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Optional)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li></ul></code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/interviews/live-status`

**Summary**: Get Live Status Dashboard

Get lightweight status summary for all active interviews.

Shows all interviews that are NOT completed/cancelled/expired.
Useful for admin dashboard to monitor multiple concurrent interviews.

Returns:
    List of active interviews with basic status, warnings, and progress

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Array<<ul><li><b>interview</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>interview_round</b>: <code>string</code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Required)</li><li><b>duration_minutes</b>: <code>integer</code> (Required)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Required)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Required)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_path</b>: <code>string</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>coding_paper_id</b>: <code>integer</code> (Optional)</li></ul></code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Required)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Required)</li><li><b>warnings_remaining</b>: <code>integer</code> (Required)</li><li><b>is_suspended</b>: <code>boolean</code> (Required)</li><li><b>last_activity</b>: <code>string</code> (Optional)</li><li><b>progress_percent</b>: <code>number</code> (Required)</li></ul>></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

---

## `GET /api/admin/interviews/{interview_id}`

**Summary**: Get Interview

Get detailed information about a specific interview session.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>number</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>coding_content</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul> | <ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<<ul><li><b>input</b>: <code>string</code> (Required)</li><li><b>output</b>: <code>string</code> (Required)</li><li><b>explanation</b>: <code>string</code> (Optional)</li></ul>></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>coding_paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>number</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>coding_content</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul> | <ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<<ul><li><b>input</b>: <code>string</code> (Required)</li><li><b>output</b>: <code>string</code> (Required)</li><li><b>explanation</b>: <code>string</code> (Optional)</li></ul>></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Optional)</li><li><b>duration_minutes</b>: <code>integer</code> (Optional)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>interview_round</b>: <code>string | string</code> (Optional)</li><li><b>response_count</b>: <code>integer</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Optional)</li><li><b>result_status</b>: <code>string</code> (Optional)</li><li><b>max_marks</b>: <code>number</code> (Optional)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_path</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_url</b>: <code>string</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>proctoring_event</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>tab_switch_count</b>: <code>integer</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Optional)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/interviews/{interview_id}`

**Summary**: Update Interview

Update interview session details (schedule_time, duration, status, paper).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>schedule_time</b>: <code>string</code> (Optional)</li><li><b>duration_minutes</b>: <code>integer</code> (Optional)</li><li><b>status</b>: <code>string</code> (Optional)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>coding_paper_id</b>: <code>integer</code> (Optional)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>number</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>coding_content</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul> | <ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<<ul><li><b>input</b>: <code>string</code> (Required)</li><li><b>output</b>: <code>string</code> (Required)</li><li><b>explanation</b>: <code>string</code> (Optional)</li></ul>></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>coding_paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>number</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>coding_content</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul> | <ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<<ul><li><b>input</b>: <code>string</code> (Required)</li><li><b>output</b>: <code>string</code> (Required)</li><li><b>explanation</b>: <code>string</code> (Optional)</li></ul>></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Optional)</li><li><b>duration_minutes</b>: <code>integer</code> (Optional)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>interview_round</b>: <code>string | string</code> (Optional)</li><li><b>response_count</b>: <code>integer</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Optional)</li><li><b>result_status</b>: <code>string</code> (Optional)</li><li><b>max_marks</b>: <code>number</code> (Optional)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_path</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_url</b>: <code>string</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>proctoring_event</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>tab_switch_count</b>: <code>integer</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Optional)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/interviews/{interview_id}`

**Summary**: Delete Interview

Hard delete an interview session and all related data (responses, proctoring events, etc.).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/candidates`

**Summary**: List Candidates

List users with CANDIDATE role with pagination and search.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/users/results`

**Summary**: Get All Results

API for the admin dashboard: Returns a flat list of candidate interview sessions and their results.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |
| `from_date` | query | No | `string` |  |
| `to_date` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>result_status</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/results/{interview_id}`

**Summary**: Get Result

Get detailed result for a specific interview session.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/results/{interview_id}`

**Summary**: Update Result

Update result scores and evaluations.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>result_status</b>: <code>string</code> (Optional)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/results/{interview_id}`

**Summary**: Delete Result

Delete all result data for an interview session (hard delete responses, keep session).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/results/{interview_id}/send-email`

**Summary**: Send Manual Result Email

Manually send the result email to the candidate.
Only works if the results have been processed (PASS/FAIL).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/interviews/response/{response_id}`

**Summary**: Get Response

Get a specific response/answer details (for audio playback etc)

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `response_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/results/audio/{response_id}`

**Summary**: Get Response Audio

Streams a candidate's audio response for review.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `response_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
any

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/interviews/enrollment-audio/{interview_id}`

**Summary**: Get Enrollment Audio

Streams the candidate's enrollment audio for verification.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
any

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/users`

**Summary**: Create User

Create a new user with resume, profile picture, and face embeddings.

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>password</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Optional)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>resume</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>resume_url</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/users`

**Summary**: List Users

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>resume_url</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/users/{user_id}`

**Summary**: Get User

Get detailed information about a specific user.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>has_profile_image</b>: <code>boolean</code> (Optional)</li><li><b>has_face_embedding</b>: <code>boolean</code> (Optional)</li><li><b>created_interviews_count</b>: <code>integer</code> (Optional)</li><li><b>participated_interviews_count</b>: <code>integer</code> (Optional)</li><li><b>resume_url</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/users/{user_id}`

**Summary**: Update User

Update user details with optional resume replacement.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>email</b>: <code>string</code> (Optional)</li><li><b>full_name</b>: <code>string</code> (Optional)</li><li><b>password</b>: <code>string</code> (Optional)</li><li><b>role</b>: <code>string</code> (Optional)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>resume</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>has_profile_image</b>: <code>boolean</code> (Optional)</li><li><b>has_face_embedding</b>: <code>boolean</code> (Optional)</li><li><b>created_interviews_count</b>: <code>integer</code> (Optional)</li><li><b>participated_interviews_count</b>: <code>integer</code> (Optional)</li><li><b>resume_url</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/users/{user_id}`

**Summary**: Delete User

Hard delete a user. All related interview sessions, results, answers,
proctoring events, and question papers are cascade-deleted by the database.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/users/{user_id}/check-delete`

**Summary**: Check Delete User

Pre-deletion dry-run check. Returns whether cascade-deleting this user
will remove related data (interviews, question papers).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/system/expire-interviews`

**Summary**: Expire Interviews Manually

Manually trigger interview expiration check.
This endpoint can be called by external cron services for platforms that don't support background processes.

For HF Spaces and Render free tier, set up a cron job to call this endpoint periodically.
Example cron: */5 * * * * curl -X POST https://your-app.com/api/admin/system/expire-interviews -H "X-CRON-SECRET: $CRON_SECRET"

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `X-CRON-SECRET` | header | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/interviews/{interview_id}/status`

**Summary**: Get Candidate Status

Get comprehensive status tracking for a single interview candidate.

Returns:
    - Full timeline of status changes
    - Warning count and violation details
    - Interview progress (questions answered/total)
    - Suspension status and reason
    - Last activity timestamp

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>interview</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>paper_id</b>: <code>integer</code> (Optional)</li><li><b>interview_round</b>: <code>string</code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Required)</li><li><b>duration_minutes</b>: <code>integer</code> (Required)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Required)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Required)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_path</b>: <code>string</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>coding_paper_id</b>: <code>integer</code> (Optional)</li></ul></code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Required)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>timeline</b>: <code>Array<<ul><li><b>status</b>: <code>string</code> (Required)</li><li><b>timestamp</b>: <code>string</code> (Required)</li><li><b>metadata</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul>></code> (Optional)</li><li><b>warnings</b>: <code><ul><li><b>total_warnings</b>: <code>integer</code> (Required)</li><li><b>warnings_remaining</b>: <code>integer</code> (Required)</li><li><b>max_warnings</b>: <code>integer</code> (Required)</li><li><b>violations</b>: <code>Array<<ul><li><b>type</b>: <code>string</code> (Required)</li><li><b>severity</b>: <code>string</code> (Required)</li><li><b>timestamp</b>: <code>string</code> (Required)</li><li><b>details</b>: <code>string</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Required)</li><li><b>progress</b>: <code><ul><li><b>questions_answered</b>: <code>integer</code> (Required)</li><li><b>total_questions</b>: <code>integer</code> (Required)</li><li><b>current_question_id</b>: <code>integer</code> (Optional)</li></ul></code> (Required)</li><li><b>is_suspended</b>: <code>boolean</code> (Required)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/super-admin/teams`

**Summary**: Create Team

Create a new team.  
Team names are **globally unique** — a 409 is returned if the name already exists.  
*(Super Admin only)*

### Request Body
<ul><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li><li><b>users</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/super-admin/teams`

**Summary**: List Teams

List all teams. Returns only basic team information without nested papers.
*(Admin + Super Admin)*

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/super-admin/teams/{team_id}`

**Summary**: Get Team

Get details of a specific team, including its question paper count.  
*(Admin + Super Admin)*

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `team_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li><li><b>users</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/super-admin/teams/{team_id}`

**Summary**: Update Team

Update a team's name or description.  
Returns 409 if the new name conflicts with another existing team.  
*(Super Admin only)*

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `team_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>name</b>: <code>string</code> (Optional)</li><li><b>description</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li><li><b>users</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/super-admin/teams/{team_id}`

**Summary**: Delete Team

Delete a team. Users in this team will have their team_id set to NULL.
*(Super Admin only)*

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `team_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/resume/`

**Summary**: Get Resume

Retrieve resume metadata for specified user_id or current user.
Admins can retrieve any, users only their own.
Allows access via interview_token for candidates.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | query | No | `integer` |  |
| `interview_token` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>user_id</b>: <code>integer</code> (Required)</li><li><b>resume_url</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>analysis</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/resume/generate-prompt/{user_id}`

**Summary**: Generate Resume Prompt

Extract text from a user's resume and generate a prompt for question generation.
Admins can generate for any user, users only for themselves.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/coding-papers/`

**Summary**: Create Coding Paper

Create a new coding question paper.

### Request Body
<ul><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>created_by</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/coding-papers/`

**Summary**: List Coding Papers

List all coding papers owned by the current admin.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>created_by</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/coding-papers/{paper_id}`

**Summary**: Get Coding Paper

Get a single coding paper with all its questions.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>created_by</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/coding-papers/{paper_id}`

**Summary**: Update Coding Paper

Update a coding paper's name or description.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>name</b>: <code>string</code> (Optional)</li><li><b>description</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul>></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>created_by</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/coding-papers/{paper_id}`

**Summary**: Delete Coding Paper

Delete a coding paper and all its questions.
Fails if the paper is linked to any scheduled or live interview.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/admin/coding-papers/{paper_id}/questions`

**Summary**: Add Coding Question

Add a new coding problem to an existing coding paper.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<Dict&lt;string, any&gt;></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>

### Responses
#### Status Code: `201`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/admin/coding-papers/{paper_id}/questions`

**Summary**: List Coding Questions

List all questions belonging to a specific coding paper.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `paper_id` | path | Yes | `integer` |  |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |
| `search` | query | No | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `PATCH /api/admin/coding-papers/questions/{q_id}`

**Summary**: Update Coding Question

Update specific fields of a coding question.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `q_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>title</b>: <code>string</code> (Optional)</li><li><b>problem_statement</b>: <code>string</code> (Optional)</li><li><b>examples</b>: <code>Array<Dict&lt;string, any&gt;></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Required)</li><li><b>problem_statement</b>: <code>string</code> (Required)</li><li><b>examples</b>: <code>Array<any></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Required)</li><li><b>difficulty</b>: <code>string</code> (Required)</li><li><b>marks</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `DELETE /api/admin/coding-papers/questions/{q_id}`

**Summary**: Delete Coding Question

Delete a coding question and update the parent paper's counts.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `q_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/otp-send`

**Summary**: Request Otp

Generate and send a 6-digit OTP to the candidate's email.
Verifies that the candidate is assigned to the provided interview link.

### Request Body
<ul><li><b>email</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/verify-otp`

**Summary**: Verify Otp

Verify the OTP code and issue a JWT access token for the candidate.

### Request Body
<ul><li><b>email</b>: <code>string</code> (Required)</li><li><b>otp</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/interview/access/{token}`

**Summary**: Access Interview

Validates the interview link and checks time constraints.
Returns a cleaned, frontend-friendly response structure.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `token` | path | Yes | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li><li><b>coding_content</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>coding_paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Optional)</li><li><b>problem_statement</b>: <code>string</code> (Optional)</li><li><b>examples</b>: <code>Array<Dict&lt;string, any&gt;></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Required)</li><li><b>duration_minutes</b>: <code>integer</code> (Required)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>interview_round</b>: <code>string</code> (Optional)</li><li><b>response_count</b>: <code>integer</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Required)</li><li><b>result_status</b>: <code>string</code> (Optional)</li><li><b>max_marks</b>: <code>number</code> (Optional)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_path</b>: <code>string</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>tab_switch_count</b>: <code>integer</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Optional)</li><li><b>tab_warning_active</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>curr_interview_timer</b>: <code>integer</code> (Optional)</li><li><b>curr_question_timer</b>: <code>integer</code> (Optional)</li><li><b>current_question_index</b>: <code>integer</code> (Optional)</li><li><b>proctoring_event</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Optional)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/interview/schedule-time/{token}`

**Summary**: Get Schedule Time

No authentication required. Used for public access to schedule information.
Checks for interview status (completed, expired, cancelled) and returns error if not accessible.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `token` | path | Yes | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
any

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/start-session/{interview_id}`

**Summary**: Start Session Logic

Called when candidate actually enters the interview session (uploads selfie/audio).
Sets status to LIVE.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>question_id</b>: <code>integer</code> (Optional)</li><li><b>coding_question_id</b>: <code>integer</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/upload-selfie`

**Summary**: Upload Selfie Session

Candidate uploads selfie during interview for face verification.
Compares uploaded selfie embeddings with stored candidate embeddings.
Returns verification result with similarity score.

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>candidate_id</b>: <code>integer</code> (Required)</li><li><b>file</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/question/next`

**Summary**: Move To Next Question

Mark current question as completed/submitted and advance to next.

Validates:
- Navigation not allowed (Case 2 enforcement)
- Cannot go backward (strict sequential order)
- Updates attempt status (submitted or expired)

Returns: new question index, total questions, completion status

### Request Body
<ul><li><b>sessionId</b>: <code>integer</code> (Required)</li><li><b>questionId</b>: <code>integer</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/interview/next-question/{interview_id}`

**Summary**: Get Next Question

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/interview/audio/question/{q_id}`

**Summary**: Stream Question Audio

Restored: Questions audio served via redirection to Cloudinary URLs.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `q_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
any

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/submit-answer-audio`

**Summary**: Submit Answer Audio

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>interview_id</b>: <code>integer</code> (Required)</li><li><b>question_id</b>: <code>integer</code> (Required)</li><li><b>audio</b>: <code>string</code> (Required)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/submit-answer-code`

**Summary**: Submit Answer Code

Submits a code answer directly.

### Request Body
Content-Type: `application/x-www-form-urlencoded`

<ul><li><b>interview_id</b>: <code>integer</code> (Required)</li><li><b>coding_question_id</b>: <code>integer</code> (Required)</li><li><b>answer_code</b>: <code>string</code> (Required)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Optional)</li><li><b>problem_statement</b>: <code>string</code> (Optional)</li><li><b>examples</b>: <code>Array<Dict&lt;string, any&gt;></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul> | Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/submit-answer-text`

**Summary**: Submit Answer Text

Submits a text answer, handles both standard and proxy-coding questions.

### Request Body
Content-Type: `application/x-www-form-urlencoded`

<ul><li><b>interview_id</b>: <code>integer</code> (Required)</li><li><b>question_id</b>: <code>integer</code> (Required)</li><li><b>answer_text</b>: <code>string</code> (Required)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li><li><b>coding_content</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul> | Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/finish/{interview_id}`

**Summary**: Finish Interview

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/evaluate-answer`

**Summary**: Evaluate Answer

Evaluates a candidate's answer against a question.

Automatically resolves the question's actual marks from the database by:
1. Using explicit question_id / coding_question_id if provided (fast path).
2. Falling back to question_marks field if provided directly.
3. Defaulting to 10 if none of the above match.

### Request Body
<ul><li><b>question</b>: <code>string</code> (Required)</li><li><b>answer</b>: <code>string</code> (Required)</li><li><b>question_id</b>: <code>integer</code> (Optional)</li><li><b>coding_question_id</b>: <code>integer</code> (Optional)</li><li><b>question_marks</b>: <code>number</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/{interview_id}/tab-switch`

**Summary**: Log Tab Switch

Logs a tab switch event during the interview.
Increments warning count and notifies admins.
Currently only generates a warning (termination logic to be enabled later).

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>event_type</b>: <code>string</code> (Optional)</li><li><b>is_active</b>: <code>boolean</code> (Optional)</li><li><b>reason</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>admin_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>candidate_user</b>: <code><ul><li><b>id</b>: <code>integer</code> (Optional)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Optional)</li><li><b>profile_image</b>: <code>string</code> (Optional)</li><li><b>team</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>user_count</b>: <code>integer</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>content</b>: <code>string</code> (Optional)</li><li><b>question_text</b>: <code>string</code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li><li><b>response_type</b>: <code>string</code> (Optional)</li><li><b>coding_content</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>coding_paper</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>name</b>: <code>string</code> (Required)</li><li><b>description</b>: <code>string</code> (Optional)</li><li><b>question_count</b>: <code>integer</code> (Optional)</li><li><b>total_marks</b>: <code>integer</code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Required)</li><li><b>team_id</b>: <code>integer</code> (Optional)</li><li><b>questions</b>: <code>Array<<ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>paper_id</b>: <code>integer</code> (Required)</li><li><b>title</b>: <code>string</code> (Optional)</li><li><b>problem_statement</b>: <code>string</code> (Optional)</li><li><b>examples</b>: <code>Array<Dict&lt;string, any&gt;></code> (Optional)</li><li><b>constraints</b>: <code>Array<string></code> (Optional)</li><li><b>starter_code</b>: <code>string</code> (Optional)</li><li><b>answer</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>interview_result_id</b>: <code>integer</code> (Required)</li><li><b>candidate_answer</b>: <code>string</code> (Optional)</li><li><b>feedback</b>: <code>string</code> (Optional)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>audio_path</b>: <code>string</code> (Optional)</li><li><b>transcribed_text</b>: <code>string</code> (Optional)</li><li><b>timestamp</b>: <code>string</code> (Required)</li></ul></code> (Optional)</li><li><b>topic</b>: <code>string</code> (Optional)</li><li><b>difficulty</b>: <code>string</code> (Optional)</li><li><b>marks</b>: <code>integer</code> (Optional)</li></ul>></code> (Optional)</li></ul></code> (Optional)</li><li><b>schedule_time</b>: <code>string</code> (Required)</li><li><b>duration_minutes</b>: <code>integer</code> (Required)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>interview_round</b>: <code>string</code> (Optional)</li><li><b>response_count</b>: <code>integer</code> (Optional)</li><li><b>last_activity</b>: <code>string</code> (Required)</li><li><b>result_status</b>: <code>string</code> (Optional)</li><li><b>max_marks</b>: <code>number</code> (Optional)</li><li><b>total_score</b>: <code>number</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>enrollment_audio_path</b>: <code>string</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>tab_switch_count</b>: <code>integer</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Optional)</li><li><b>tab_warning_active</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li><li><b>curr_interview_timer</b>: <code>integer</code> (Optional)</li><li><b>curr_question_timer</b>: <code>integer</code> (Optional)</li><li><b>current_question_index</b>: <code>integer</code> (Optional)</li><li><b>proctoring_event</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>max_warnings</b>: <code>integer</code> (Optional)</li><li><b>is_suspended</b>: <code>boolean</code> (Optional)</li><li><b>suspension_reason</b>: <code>string</code> (Optional)</li><li><b>suspended_at</b>: <code>string</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li><li><b>allow_question_navigate</b>: <code>boolean</code> (Optional)</li><li><b>allow_proctoring</b>: <code>boolean</code> (Optional)</li></ul></code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/tools/speech-to-text`

**Summary**: Speech To Text Tool

Public standalone tool to convert speech to text.

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>audio</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/interview/tools/sttEvaluate`

**Summary**: Stt Evaluate Tool

Standalone tool to convert speech to text AND evaluate it against a question.

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>audio</b>: <code>string</code> (Required)</li><li><b>question_text</b>: <code>string</code> (Required)</li><li><b>expected_answer</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/interview/tts`

**Summary**: Standalone Tts

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `text` | query | Yes | `string` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
any

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/candidate/history`

**Summary**: My History

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>interview_id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>paper_name</b>: <code>string</code> (Required)</li><li><b>date</b>: <code>string</code> (Required)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>duration_minutes</b>: <code>integer</code> (Optional)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/candidate/interviews`

**Summary**: My Interviews

Fetch scheduled and upcoming interviews for the candidate.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `skip` | query | No | `integer` |  |
| `limit` | query | No | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>items</b>: <code>Array<<ul><li><b>interview_id</b>: <code>integer</code> (Required)</li><li><b>access_token</b>: <code>string</code> (Required)</li><li><b>paper_name</b>: <code>string</code> (Required)</li><li><b>date</b>: <code>string</code> (Required)</li><li><b>status</b>: <code>string</code> (Required)</li><li><b>score</b>: <code>number</code> (Optional)</li><li><b>duration_minutes</b>: <code>integer</code> (Optional)</li><li><b>max_questions</b>: <code>integer</code> (Optional)</li><li><b>start_time</b>: <code>string</code> (Optional)</li><li><b>end_time</b>: <code>string</code> (Optional)</li><li><b>warning_count</b>: <code>integer</code> (Optional)</li><li><b>is_completed</b>: <code>boolean</code> (Optional)</li><li><b>current_status</b>: <code>string</code> (Optional)</li><li><b>allow_copy_paste</b>: <code>boolean</code> (Optional)</li></ul>></code> (Required)</li><li><b>total</b>: <code>integer</code> (Required)</li><li><b>skip</b>: <code>integer</code> (Required)</li><li><b>limit</b>: <code>integer</code> (Required)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/candidate/upload-selfie`

**Summary**: Upload Selfie

Candidate uploads their own selfie for face enrollment and identity verification.
Generates face embeddings (ArcFace + SFace) for proctoring during interview.
Optionally updates interview status to SELFIE_UPLOADED if interview_id provided.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | query | No | `integer` |  |

### Request Body
Content-Type: `multipart/form-data`

<ul><li><b>file</b>: <code>string</code> (Required)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/candidate/profile-image/{user_id}`

**Summary**: Get Profile Image

Streams the user's profile image (selfie) directly to the browser.

Returns:
    - Raw image bytes with appropriate Content-Type header if image found
    - 404 if no image exists

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `user_id` | path | Yes | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
any

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/candidate/profile/me`

**Summary**: Get My Profile

Retrieve the current candidate's profile and details.

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>details</b>: <code><ul><li><b>date_of_birth</b>: <code>string</code> (Optional)</li><li><b>gender</b>: <code>string</code> (Optional)</li><li><b>blood_group</b>: <code>string</code> (Optional)</li><li><b>nationality</b>: <code>string</code> (Optional)</li><li><b>religion</b>: <code>string</code> (Optional)</li><li><b>marital_status</b>: <code>string</code> (Optional)</li><li><b>father_name</b>: <code>string</code> (Optional)</li><li><b>mother_name</b>: <code>string</code> (Optional)</li><li><b>guardian_name</b>: <code>string</code> (Optional)</li><li><b>guardian_relation</b>: <code>string</code> (Optional)</li><li><b>phone_number</b>: <code>string</code> (Optional)</li><li><b>alternate_phone</b>: <code>string</code> (Optional)</li><li><b>address_line1</b>: <code>string</code> (Optional)</li><li><b>address_line2</b>: <code>string</code> (Optional)</li><li><b>city</b>: <code>string</code> (Optional)</li><li><b>state</b>: <code>string</code> (Optional)</li><li><b>postal_code</b>: <code>string</code> (Optional)</li><li><b>country</b>: <code>string</code> (Optional)</li><li><b>aadhar_number</b>: <code>string</code> (Optional)</li><li><b>pan_number</b>: <code>string</code> (Optional)</li><li><b>passport_number</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_name</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_phone</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_relation</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>updated_at</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

---

## `DELETE /api/candidate/profile/me`

**Summary**: Delete My Profile

Delete the current candidate's account and all associated data.

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

---

## `PATCH /api/candidate/profile/me`

**Summary**: Update My Profile

Update the current candidate's profile and details.

### Request Body
<ul><li><b>date_of_birth</b>: <code>string</code> (Optional)</li><li><b>gender</b>: <code>string</code> (Optional)</li><li><b>blood_group</b>: <code>string</code> (Optional)</li><li><b>nationality</b>: <code>string</code> (Optional)</li><li><b>religion</b>: <code>string</code> (Optional)</li><li><b>marital_status</b>: <code>string</code> (Optional)</li><li><b>father_name</b>: <code>string</code> (Optional)</li><li><b>mother_name</b>: <code>string</code> (Optional)</li><li><b>guardian_name</b>: <code>string</code> (Optional)</li><li><b>guardian_relation</b>: <code>string</code> (Optional)</li><li><b>phone_number</b>: <code>string</code> (Optional)</li><li><b>alternate_phone</b>: <code>string</code> (Optional)</li><li><b>address_line1</b>: <code>string</code> (Optional)</li><li><b>address_line2</b>: <code>string</code> (Optional)</li><li><b>city</b>: <code>string</code> (Optional)</li><li><b>state</b>: <code>string</code> (Optional)</li><li><b>postal_code</b>: <code>string</code> (Optional)</li><li><b>country</b>: <code>string</code> (Optional)</li><li><b>aadhar_number</b>: <code>string</code> (Optional)</li><li><b>pan_number</b>: <code>string</code> (Optional)</li><li><b>passport_number</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_name</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_phone</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_relation</b>: <code>string</code> (Optional)</li><li><b>full_name</b>: <code>string</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code><ul><li><b>id</b>: <code>integer</code> (Required)</li><li><b>email</b>: <code>string</code> (Required)</li><li><b>full_name</b>: <code>string</code> (Required)</li><li><b>role</b>: <code>string</code> (Required)</li><li><b>details</b>: <code><ul><li><b>date_of_birth</b>: <code>string</code> (Optional)</li><li><b>gender</b>: <code>string</code> (Optional)</li><li><b>blood_group</b>: <code>string</code> (Optional)</li><li><b>nationality</b>: <code>string</code> (Optional)</li><li><b>religion</b>: <code>string</code> (Optional)</li><li><b>marital_status</b>: <code>string</code> (Optional)</li><li><b>father_name</b>: <code>string</code> (Optional)</li><li><b>mother_name</b>: <code>string</code> (Optional)</li><li><b>guardian_name</b>: <code>string</code> (Optional)</li><li><b>guardian_relation</b>: <code>string</code> (Optional)</li><li><b>phone_number</b>: <code>string</code> (Optional)</li><li><b>alternate_phone</b>: <code>string</code> (Optional)</li><li><b>address_line1</b>: <code>string</code> (Optional)</li><li><b>address_line2</b>: <code>string</code> (Optional)</li><li><b>city</b>: <code>string</code> (Optional)</li><li><b>state</b>: <code>string</code> (Optional)</li><li><b>postal_code</b>: <code>string</code> (Optional)</li><li><b>country</b>: <code>string</code> (Optional)</li><li><b>aadhar_number</b>: <code>string</code> (Optional)</li><li><b>pan_number</b>: <code>string</code> (Optional)</li><li><b>passport_number</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_name</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_phone</b>: <code>string</code> (Optional)</li><li><b>emergency_contact_relation</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>created_at</b>: <code>string</code> (Optional)</li><li><b>updated_at</b>: <code>string</code> (Optional)</li></ul></code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/video/status`

**Summary**: Proctoring Status

Returns the current proctoring warning and detection details for a session.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `interview_id` | query | No | `integer` |  |

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
any

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `GET /api/video/credentials`

**Summary**: Get Webrtc Credentials

Returns the ICE/TURN server configuration from environment variables.
This allows the client to avoid hardcoding sensitive credentials.

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

---

## `POST /api/video/offer`

**Summary**: Offer

Candidate Connection (Proctoring Source). 
Registers identity and initializes session-isolated AI.

### Request Body
<ul><li><b>sdp</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li><li><b>interview_id</b>: <code>integer</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

## `POST /api/video/watch/{target_session_id}`

**Summary**: Watch

Admin Ghost Mode: Watch an active session.
Waits up to 10 seconds for candidate stream to be available.

### Parameters
| Name | Located in | Required | Type | Description |
| --- | --- | --- | --- | --- |
| `target_session_id` | path | Yes | `integer` |  |

### Request Body
<ul><li><b>sdp</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li><li><b>interview_id</b>: <code>integer</code> (Optional)</li></ul>

### Responses
#### Status Code: `200`
**Description**: Successful Response

**Response Schema**:
<ul><li><b>status_code</b>: <code>integer</code> (Optional)</li><li><b>data</b>: <code>Dict&lt;string, any&gt;</code> (Optional)</li><li><b>message</b>: <code>string</code> (Optional)</li><li><b>success</b>: <code>boolean</code> (Optional)</li></ul>

#### Status Code: `422`
**Description**: Validation Error

**Response Schema**:
<ul><li><b>detail</b>: <code>Array<<ul><li><b>loc</b>: <code>Array<string | integer></code> (Required)</li><li><b>msg</b>: <code>string</code> (Required)</li><li><b>type</b>: <code>string</code> (Required)</li></ul>></code> (Optional)</li></ul>

---

