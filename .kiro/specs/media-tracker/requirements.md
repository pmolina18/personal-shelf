# Requirements Document — Media Tracker

## Introduction

Media Tracker is a personal web application for recording and managing media consumption: movies, books, and TV series. The application consists of a Vue.js frontend, a Python backend, and a PostgreSQL database. The goal is for the user to be able to save, organize, search, and track the media they consume, including its status (pending, in progress, completed) and a personal rating.

## Glossary

- **System**: The Media Tracker application as a whole (frontend + backend + database).
- **API**: The Python backend service that exposes REST endpoints for managing data.
- **Client**: The Vue.js frontend application that consumes the API.
- **Media_Item**: An individual record representing a movie, book, or series.
- **Media_Type**: The category of the item: movie, book, or series.
- **Status**: The consumption status of a Media_Item: "pending", "in_progress", or "completed".
- **Rating**: A numeric score from 1 to 10 assigned by the user to a Media_Item.
- **Catalog**: The complete collection of the user's Media_Items.
- **Tag**: A user-defined keyword for classifying Media_Items (e.g., "science fiction", "horror", "classic").
- **MCP_Server**: A server that implements the Model Context Protocol (MCP) and exposes the API functionalities as tools invocable by AI assistants.
- **MCP**: Model Context Protocol, a standard protocol that allows AI assistants to discover and invoke tools exposed by external servers.
- **Media_Image**: An image associated with a Media_Item (e.g., movie poster, book cover, series poster) automatically downloaded from the internet.
- **Image_Service**: The backend component responsible for searching and downloading relevant images from external sources on the internet.

## Requirements

### Requirement 1: Create a Media Item

**User Story:** As a user, I want to add a new movie, book, or series to my catalog, so that I can record the media I consume or plan to consume.

#### Acceptance Criteria

1. WHEN the user submits a form with title, Media_Type, and optionally year, author/director, and notes, THE API SHALL create a new Media_Item in the database and return the created Media_Item with a unique identifier.
2. WHEN the user does not provide a title, THE API SHALL return a validation error with code 400 indicating that the title is required.
3. WHEN the user does not provide a valid Media_Type, THE API SHALL return a validation error with code 400 indicating the allowed types (movie, book, series).
4. THE API SHALL assign the Status "pending" by default to each new Media_Item created.

### Requirement 2: List the Catalog

**User Story:** As a user, I want to see all the media I have recorded, so that I can browse my complete catalog.

#### Acceptance Criteria

1. WHEN the user requests the catalog, THE API SHALL return a paginated list of Media_Items sorted by creation date in descending order.
2. WHEN the catalog is empty, THE Client SHALL display a message indicating that there are no recorded items and a button to add the first one.
3. THE Client SHALL display for each Media_Item: title, Media_Type, Status, and Rating (if it exists).

### Requirement 3: Filter and Search Media Items

**User Story:** As a user, I want to filter and search my catalog, so that I can quickly find a specific media item.

#### Acceptance Criteria

1. WHEN the user applies a filter by Media_Type, THE API SHALL return only the Media_Items that match the selected Media_Type.
2. WHEN the user applies a filter by Status, THE API SHALL return only the Media_Items that match the selected Status.
3. WHEN the user enters a search text, THE API SHALL return the Media_Items whose title contains the provided text, case-insensitively.
4. WHEN the user combines Media_Type, Status, and search text filters, THE API SHALL apply all filters jointly (logical AND).

### Requirement 4: Edit a Media Item

**User Story:** As a user, I want to modify the data of a recorded media item, so that I can correct errors or update information.

#### Acceptance Criteria

1. WHEN the user submits changes for an existing Media_Item, THE API SHALL update the provided fields and return the updated Media_Item.
2. WHEN the user attempts to edit a Media_Item that does not exist, THE API SHALL return an error with code 404.
3. THE API SHALL validate the edited fields with the same rules as creation (title required, valid Media_Type).

### Requirement 5: Delete a Media Item

**User Story:** As a user, I want to delete a media item from my catalog, so that I can keep my collection clean and relevant.

#### Acceptance Criteria

1. WHEN the user requests to delete a Media_Item, THE Client SHALL ask for confirmation before executing the deletion.
2. WHEN the user confirms the deletion, THE API SHALL delete the Media_Item from the database and return code 204.
3. WHEN the user attempts to delete a Media_Item that does not exist, THE API SHALL return an error with code 404.

### Requirement 6: Manage Consumption Status

**User Story:** As a user, I want to change the status of a media item (pending, in progress, completed), so that I can track what I am consuming.

#### Acceptance Criteria

1. WHEN the user changes the Status of a Media_Item to "completed", THE API SHALL automatically record the completion date.
2. WHEN the user changes the Status of a Media_Item to "in_progress", THE API SHALL automatically record the start date (if one did not previously exist).
3. IF the user provides a Status that is not "pending", "in_progress", or "completed", THEN THE API SHALL return a validation error with code 400.

### Requirement 7: Rate a Media Item

**User Story:** As a user, I want to rate the media I have consumed, so that I can remember my opinion about each one.

#### Acceptance Criteria

1. WHEN the user assigns a Rating to a Media_Item, THE API SHALL save the score associated with the Media_Item.
2. IF the Rating provided is not an integer between 1 and 10, THEN THE API SHALL return a validation error with code 400.
3. WHILE the Status of a Media_Item is "pending", THE Client SHALL disable the Rating field and indicate that the media item must be in progress or completed to be rated.

### Requirement 8: Manage Tags

**User Story:** As a user, I want to assign custom tags to my media items, so that I can organize them by genre, theme, or other personal criteria.

#### Acceptance Criteria

1. WHEN the user assigns one or more Tags to a Media_Item, THE API SHALL save the Tags associated with the Media_Item.
2. WHEN the user filters by a Tag, THE API SHALL return all Media_Items that have the specified Tag assigned.
3. THE API SHALL allow a maximum of 10 Tags per Media_Item.
4. IF the user attempts to assign more than 10 Tags to a Media_Item, THEN THE API SHALL return a validation error with code 400 indicating the limit.

### Requirement 9: View Catalog Statistics

**User Story:** As a user, I want to see statistics about my media consumption, so that I can understand my habits and trends.

#### Acceptance Criteria

1. WHEN the user requests statistics, THE API SHALL return the total number of Media_Items grouped by Media_Type.
2. WHEN the user requests statistics, THE API SHALL return the total number of Media_Items grouped by Status.
3. WHEN the user requests statistics, THE API SHALL return the average Rating grouped by Media_Type (considering only Media_Items with an assigned Rating).

### Requirement 10: Data Persistence and Serialization

**User Story:** As a user, I want my data to be stored reliably and to be exportable, so that I do not lose my catalog.

#### Acceptance Criteria

1. THE API SHALL store all Media_Items in the PostgreSQL database persistently.
2. WHEN the user requests to export the catalog, THE API SHALL generate a JSON file with all Media_Items and their associated data.
3. WHEN the user imports a JSON file, THE API SHALL parse the content and create the corresponding Media_Items in the database.
4. FOR ALL valid Media_Items, exporting to JSON and then importing the resulting JSON SHALL produce Media_Items equivalent to the originals (round-trip property).

### Requirement 11: MCP Server for Natural Language Interaction

**User Story:** As a user, I want to be able to manage my media catalog through natural language text (via an AI assistant), so that I can add, delete, update, and query items without using the graphical interface.

#### Acceptance Criteria

1. THE API SHALL expose an MCP (Model Context Protocol) server that registers tools equivalent to the REST endpoints of the backend.
2. WHEN an AI assistant invokes the MCP creation tool, THE MCP_Server SHALL create a new Media_Item with the provided parameters, applying the same validation rules as the corresponding REST endpoint.
3. WHEN an AI assistant invokes the MCP deletion tool with an identifier, THE MCP_Server SHALL delete the corresponding Media_Item, applying the same rules as the corresponding REST endpoint.
4. WHEN an AI assistant invokes the MCP update tool with an identifier and fields to modify, THE MCP_Server SHALL update the corresponding Media_Item, applying the same validation rules as the corresponding REST endpoint.
5. WHEN an AI assistant invokes the MCP listing tool, THE MCP_Server SHALL return the paginated list of Media_Items, accepting the same filter and search parameters as the corresponding REST endpoint.
6. WHEN an AI assistant invokes the MCP status change tool, THE MCP_Server SHALL update the Status of the Media_Item, applying the same transition and date recording rules as the corresponding REST endpoint.
7. WHEN an AI assistant invokes the MCP rating tool, THE MCP_Server SHALL assign the Rating to the Media_Item, applying the same validation rules as the corresponding REST endpoint.
8. WHEN an AI assistant invokes the MCP tag management tool, THE MCP_Server SHALL add or remove Tags from the Media_Item, applying the same rules and limits as the corresponding REST endpoint.
9. WHEN an AI assistant invokes the MCP statistics tool, THE MCP_Server SHALL return the same statistics as the corresponding REST endpoint.
10. WHEN an AI assistant invokes the MCP export or import tool, THE MCP_Server SHALL execute the export or import applying the same rules as the corresponding REST endpoint.
11. IF an MCP tool receives invalid parameters, THEN THE MCP_Server SHALL return a descriptive error message in a format readable by the AI assistant.
12. THE MCP_Server SHALL describe each tool with a name, a natural language description, and a JSON schema of the accepted parameters, in accordance with the MCP specification.

### Requirement 12: Image Associated with Media Item

**User Story:** As a user, I want each media item in my catalog to have a representative image (poster, cover), so that I can visually identify the items in my collection.

#### Acceptance Criteria

1. WHEN the user creates a new Media_Item with title and Media_Type, THE Image_Service SHALL automatically search for a relevant image on the internet (movie poster, book cover, or series poster) and associate it with the Media_Item.
2. WHEN the user updates the title or Media_Type of a Media_Item, THE Image_Service SHALL search for a new image matching the updated title and Media_Type and replace the previous Media_Image.
3. THE API SHALL store the downloaded Media_Image on the server and return an accessible URL so that the Client can display it.
4. WHEN the Client displays a Media_Item, THE Client SHALL show the associated Media_Image alongside the title, Media_Type, Status, and Rating.
5. IF the Image_Service does not find any relevant image for a Media_Item, THEN THE API SHALL assign a default generic image based on the Media_Type (one default image for movies, another for books, and another for series).
6. WHEN the user requests to export the catalog to JSON, THE API SHALL include the Media_Image URL of each Media_Item in the exported data.
7. THE API SHALL expose an endpoint that allows querying the Media_Image of a Media_Item given its identifier.
