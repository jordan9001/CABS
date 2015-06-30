# CABS
Connection Automation/Brokerage System

##Overview
A CABS implementation consists of 3 main parts:

###The Client
- On user's machines.
- A GUI for connections.
- Authenticates the User, and returns available pools.
- Can start an RGS session with RGS Receiver.
- Available as a desktop application on Windows, Linux, and Macintosh.
- Configurable via a configuration file (can be distributed with proper default configurations).

###The Agent
- On a machine containing the RGS sender.
- Sends a status report to the Broker on a set interval.
- Confirms users currently logged into that machine.
- Available as an application on Windows or Linux.
- Configurable via a configuration file (can be distributed with proper default configurations).

###The Broker
- Our server that communicates between the Client and the Agent.
- Tracks free machines via a database.
- Machines are organized by "Pools" and pools can specify secondary pools for backup.
- Tracks usage history, and configuration history.
- Configuration and monitoring can be done via a web interface.
- Setup settings are stored in a configuration file.


