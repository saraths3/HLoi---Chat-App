# Hloi

Hloi is a real-time chat application built with Django, Django Channels, WebSockets, Redis and HTMX.

It supports private conversations and multi-user channels with real-time messaging.

## Features

| Feature       | Description                                       |
| ------------- | ------------------------------------------------- |
| Social Login  | Google and GitHub                                 |
| Direct Chat   | One-to-one real-time messaging                    |
| Channels      | Multi-user group conversations                    |
| Profiles      | User profiles with username, name and avatar      |
| Friends       | Search and manage friends                         |
| Real-time     | WebSocket-based messaging                         |
| Database      | SQLite for development, PostgreSQL for production |
| Channel Layer | Redis / Valkey                                    |
| Frontend      | HTML, CSS and HTMX                                |

## Tech Stack

| Technology      | Purpose                   |
| --------------- | ------------------------- |
| Python          | Main programming language |
| Django          | Web framework             |
| Django Channels | WebSocket support         |
| HTMX            | Dynamic frontend updates  |
| Redis / Valkey  | Channel layer             |
| PostgreSQL      | Production database       |
| Daphne          | ASGI server               |
| Django Allauth  | Social authentication     |

## Architecture

```text
                    Hloi
                     |
          +----------+----------+
          |                     |
        HTTP                 WebSocket
          |                     |
       Django               Channels
          |                     |
          |                 Consumers
          |                     |
          +----------+----------+
                     |
                 Database
                     |
                   Redis
```

## How Real-time Chat Works

```text
User sends message
        |
        v
    WebSocket
        |
        v
      Consumer
        |
        +------> Save to Database
        |
        v
   Redis Channel Layer
        |
        v
   Conversation Group
        |
        v
Connected Users
        |
        v
      HTMX
        |
        v
Updated Chat
```

The browser keeps a WebSocket connection open while the user is chatting.

When a message is sent, the consumer saves it to the database and broadcasts it through the conversation's channel group.

All connected users in that group receive the message without refreshing the page.

## Direct Chat

Each direct conversation has its own channel group.

```text
User A ──┐
         ├──> conversation_15
User B ──┘
```

A message sent by either user is broadcast to the same group.

## Channels

Channels work in the same way but can contain multiple users.

```text
User A ──┐
User B ──┤
User C ──┼──> channel_7
User D ──┘
```

Only members of the channel can connect to its WebSocket group.

## Redis

Redis is used as the Django Channels channel layer.

It allows WebSocket consumers to communicate through a shared layer.

```text
Consumer
    |
    v
  Redis
    |
    v
Other Consumers
    |
    v
Connected Users
```

UUID and datetime values are converted to strings before being sent through Redis so they can be serialized safely.

## Authentication

Hloi uses social authentication through Django Allauth.

Currently supported:

* Google
* GitHub

Traditional username and password authentication is not used.

## Project Structure

```text
hloi/
├── accounts/
│   └── CustomUser
├── core/
│   ├── Profile
│   └── Friendship
├── chat/
│   ├── Conversation
│   ├── Message
│   └── Consumers
└── config/
    └── ASGI
```

## HTTP vs WebSocket

| HTTP                | WebSocket                 |
| ------------------- | ------------------------- |
| Load pages          | Real-time messaging       |
| Authentication      | Receive messages          |
| Profiles            | Send messages             |
| Friends             | Broadcast messages        |
| Load chat history   | Manage connections        |
| Normal Django views | Django Channels consumers |

## Main Flow

```text
Login
  ↓
Profile
  ↓
Friends
  ↓
Conversation
  ↓
WebSocket Connection
  ↓
Django Channels
  ↓
Redis
  ↓
Real-time Messages
```

## Deployment

Hloi is designed to run with an ASGI server because the application uses WebSockets.

Production setup:

```text
Browser
   |
 HTTPS
   |
Hosting Platform
   |
   +── Django / Daphne
   |
   +── PostgreSQL
   |
   +── Redis
```

## Purpose

Hloi was built as a practical Django project to learn and implement:

* Django
* Authentication
* Database relationships
* WebSockets
* Django Channels
* Redis
* HTMX
* ASGI
* Real-time communication
* Django deployment
