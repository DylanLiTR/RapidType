# RapidType Privacy Policy

Effective Date: June 13, 2026

This Privacy Policy explains how RapidType collects, uses, and stores data. By adding RapidType to your server or interacting with it, you agree to the terms outlined below.

## 1. Data We Collect

We only collect the minimal amount of data necessary to provide typing tests and track user statistics. This data includes:

- User IDs and Display Names: To save your lifetime typing statistics (WPM, CPM, accuracy, total typing time, and tests completed).
- Server (Guild) IDs: To store customized server prefixes and manage server-specific custom quote pools.
- Message Metadata: Temporary processing of message channels and message content to verify your typing test inputs against the selected quote.

## 2. How We Use Data

Collected data is used strictly for the core functionality of RapidType:

- Calculating typing performance metrics (WPM, CPM, Accuracy).
- Displaying server-specific stats profiles.
- Restricting command parsing based on administrator permissions.

We never sell, rent, or share your data with third parties.

## 3. Data Storage & Security

All data is stored in a private, encrypted SQLite local database hosted securely on our hosting infrastructure. We do not transmit your personal data to external APIs or third-party cloud data warehouses.

## 4. Data Deletion and User Rights

You have full control over your data.

- Custom Quotes: Server administrators can remove any custom-added server quote at any time using the >delete [ID] command.
- Account Deletion: If you wish to purge your typing history and statistics permanently from our SQLite database, you may contact the developer directly by DMing `lei3864`.
- Server Removal: If a server kicks or bans RapidType, your server prefix configuration remains in the database but can be purged upon explicit request.
