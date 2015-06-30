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
