# CABS
Connection Automation/Brokerage System

##Overview
A CABS implementation would consist of 3 main parts:

###The Client
- On a machine containing the RGS Receiver.
- A GUI for connections.
- Authenticates the User, and returns available pools.
- Starts an RGS session.
- Available as a desktop application on Windows, Linux, and Macintosh.
- Configurable via a configuration file (can be distributed with proper default configurations).

###The Agent
- On a machine containing the RGS sender.
- Sends a status report to the Broker every 3 minutes.
- Confirms login connections made or logout.
- Available as an application on Windows or Linux.
- Configurable via a configuration file (can be distributed with proper default configurations).

###The Broker
- Our server that communicates between the Client and the Agent.
- Tracks free machines via a mySQL database.
- Machines are organized by "Pools" and pools can specify secondary pools for backup.
- Tracks usage history, and configuration history.
- By default will blacklist any IP address that tries to connect too many times per minute.
- Configuration and monitoring is done via a web interface.
- Common Configuration settings are stored in database.
- Setup settings are stored in a configuration file.


##Typical Sequence of Events
1. The Client sends a secure request to the Broker with user credentials, and the machines RGS version.
2. The Broker confirms the RGS version number, the user's credentials, and returns available machine pools.
3. The Client chooses from a machine pool.
4. The Broker finds an open blade in the pool's database, and puts an entry in the database assigning that user to the machine.
5. The Broker sends the client the connection information.
6. The Client opens an RGS connection to the blade with the given information.
7. The Agent on the blade confirms a connection to the Broker.
8. The Broker marks the connection as confirmed in the database, and makes a note in the log file.
9. On confirmed logoff the Agent tells the Broker the machine is free again.
10. The Broker makes a note in the log, then removes the entry from the database.


##Technical details
The Broker will be written in python, relying on the Twisted python package, which is an event-driven networking engine.
Another option would be the Tornado library, but in this case tornado would not provide any real advantage.
The typical speed bottleneck for this system will be the database server.

###Information on twisted:
Twisted is a event-driven networking engine, to allow asynchronous socket connection handling.
Twisted is licensed under the open source MIT license.
Twisted has a very clear API, and provides simplicity while adding security and speed.
All open tickets for twisted are not applicable bugs to this project, which will just be using a handful of the core functions.
Twisted has a nice add on to work directly with LDAP, for our authentication needs.

###Security details:
- DOS attack protection:
- The Broker will blacklist any addresses that tries to connect too many times per minute, and notify the administrator.
- The Broker will blacklist any addresses that give incorrect credentials too many times per hour, and notify the administrator.

####Information Security:
- All communication between the Client and Broker, the Broker and Database, or the Agent and Broker will be secured with SSL protocol.

####Injection/Fuzzing
- The only user defined input that will be processed in a database call is their username and possibly password, which will be sanitized of restricted characters.
- The Broker never executes any commands containing user input.
- The Broker does not unpack any pickle modules recieved, and will not compile any code modules.
- The Client only accepts data from the Broker's address, and only on a connection The Client initiated.
- The Client checks any data from the Broker, to make sure the data is in the correct format.

####Buffer Overflow
- Both CABS and the library "twisted" are written in Python, a high-level language, rendering them immune to Buffer Overflow, the most common class of security flaw in network software.
