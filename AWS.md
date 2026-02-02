# AWS Architecture

Create the following architecture to move the applicaiton to AWS

## Phase 1: Foundation (Network & Storage)

* [x] Create VPC: Ensure it has an Internet Gateway attached.

* [x] Create Public Subnets: You need at least 2 public subnets (mapped to different Availability Zones) for the MSK cluster.

* [x] Create DynamoDB Table:

Name: StandaloneUserHashes.

Partition Key: email (String).

Encryption: Default (AWS Owned Key).

## Phase 2: The Pipe (MSK Setup)

* [x] Deploy MSK Cluster:

Subnets: Select the Public Subnets created in Phase 1.

* [x] Configure Networking:

Enable Public Access for brokers.

* [x] Configure Security:

Authentication: Enable IAM Access Control.

* [x] Update Security Groups:

Add Inbound Rule: Allow TCP port 9198 from your Local Machine's IP (for the Producer).

Add Inbound Rule: Allow TCP port 9098 from the Loader Lambda's Security Group (internal traffic).

## Phase 3: The Code (Lambdas & Layers)

* [x] Build Lambda Layer:

Create a zip file containing passlib (and bcrypt/argon2 matches your local DB).

Upload to AWS Lambda > Layers.

* [ ] Create "Loader" Lambda:

Code: Parses MSK JSON -> Writes to DynamoDB.

IAM Role: Add dynamodb:PutItem (for LegacyUserHashes) and AWSKafka:Read.

Network: Place in the Private Subnet (with NAT Gateway) OR Public Subnet (if simple config).

Trigger: Add MSK Trigger (Batch size ~100).

* [ ] Create "Migration" Lambda:

Code: Input Password -> Fetch DynamoDB Hash -> passlib.verify() -> Return Success JSON.

Layers: Attach the passlib layer created above.

IAM Role: Add dynamodb:GetItem (for LegacyUserHashes).

## Phase 4: The Identity Provider (Cognito)

* [ ] Create User Pool: Standard setup (Email as sign-in).

* [ ] Configure App Client:

Critical: Enable ALLOW_USER_PASSWORD_AUTH in the authentication flows settings.

Why: The migration trigger requires the plain-text password to be passed to the Lambda.

* [ ] Link Trigger:

Go to User Pool Properties > User Migration Trigger.

Select the Migration Lambda created in Phase 3.

## Phase 5: Execution

* [ ] Run Local Producer:

Script: Reads Local Postgres -> Sends JSON (email, hash, profile) to MSK Public Endpoint (b-1.public...:9198).

Verify: Check DynamoDB table to ensure data is staged.

* [ ] Update Frontend:

Point login form to Cognito.

* [ ] Test Login:

Attempt login with a legacy user account.

Verify the user is successfully migrated to Cognito and the token is returned.