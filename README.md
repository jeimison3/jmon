# JMON
A simple tool for status management of various servers, services, endpoints, connections, logs and more.


## Progress
| TODO   |  WIP   | Done   |
| ------ | ------ | ------ |
| MySQL  | Ping   | TCP    |
| DNS    | HTTP   | TCP6   |
| File   |        |        |

### Features:
- TODO: Specify bad signals.
- TODO: Watch file updates, "grep" or "regex".

## Files and structure
- env.yaml: Client-side JMON settings. `Template: env.client.yaml`
- env.ser.yaml: Server-side JMON settings. `Template: env.server.yaml`
- /profiles/[example-alias].yaml: Server-side parameters for watching on [example-alias] client. `Template: profiles/example-alias.yaml`