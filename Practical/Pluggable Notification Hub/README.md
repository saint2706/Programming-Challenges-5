# Pluggable Notification Hub

A small, configuration-driven hub for fanning out notifications to multiple providers. Providers are loaded dynamically from built-ins, Python entry points, or a plugins directory.

## Features

- Abstract `NotificationProvider` with a simple `send(message, recipient)` interface.
- Built-in mock providers: Email, Slack, and SMS.
- Plugin discovery via entry points or a `plugins` folder.
- Configuration file support (JSON or YAML) for enabling providers and supplying their options.
- Dispatcher that broadcasts notifications to every enabled provider.

## Package Layout

- `providers/base.py`: `NotificationProvider` interface.
- `providers/email.py`, `providers/slack.py`, `providers/sms.py`: built-in providers.
- `providers/__init__.py`: discovery helpers for built-ins, entry points, and a plugins directory.
- `config.py`: configuration parsing helpers.
- `dispatcher.py`: fan-out dispatcher for sending a message to all configured providers.

## Example configuration

`config.yaml`:

```yaml
providers:
  - name: email
    enabled: true
    options:
      smtp_server: smtp.example.com
      sender: notifications@example.com
  - name: slack
    enabled: true
    options:
      webhook_url: https://hooks.slack.com/services/T000/B000/XXXX
      channel: '#alerts'
  - name: sms
    enabled: false # disable temporarily
plugins_dir: ./plugins # optional, for local plugin modules
entry_point_group: notification_providers
```

Equivalent JSON:

```json
{
  "providers": [
    {
      "name": "email",
      "enabled": true,
      "options": {
        "smtp_server": "smtp.example.com",
        "sender": "notifications@example.com"
      }
    },
    {
      "name": "slack",
      "enabled": true,
      "options": {
        "webhook_url": "https://hooks.slack.com/services/T000/B000/XXXX",
        "channel": "#alerts"
      }
    },
    { "name": "sms", "enabled": false, "options": { "gateway": "twilio" } }
  ],
  "plugins_dir": "./plugins",
  "entry_point_group": "notification_providers"
}
```

## Usage

Because the package lives in a directory with spaces, load it via `importlib` and register the module name so plugin modules can import it:

```python
import sys
from importlib import util
from pathlib import Path

package_root = Path("Practical/Pluggable Notification Hub")
spec = util.spec_from_file_location(
    "pluggable_notification_hub", package_root / "__init__.py"
)
module = util.module_from_spec(spec)
sys.modules[spec.name] = module  # make it importable for plugins
assert spec.loader
spec.loader.exec_module(module)

settings = module.load_settings(Path("config.yaml"))
providers = module.initialize_providers(
    settings.providers,
    entry_point_group=settings.entry_point_group,
    plugins_dir=settings.plugins_dir,
)
dispatcher = module.NotificationDispatcher(providers)

dispatcher.notify_all(
    message="Backup completed successfully.",
    recipient="team@example.com",  # interpreted per provider
)
```

## Writing a plugin

Create a Python module in your `plugins_dir` that exposes a subclass of `NotificationProvider` via a module-level `provider` variable. The example below imports the base class through the registered module name used in the usage snippet above:

```python
# plugins/pushbullet_plugin.py
from pluggable_notification_hub.providers import NotificationProvider

class PushbulletProvider(NotificationProvider):
    def send(self, message: str, recipient: str) -> None:
        token = self.options.get("token")
        print(f"[Pushbullet] To: {recipient} | Token: {token} | Message: {message}")

provider = PushbulletProvider
```

The hub will load the module, read the `provider` variable, and instantiate it using the options from your config file.

## Notes

- The built-in providers print to stdout instead of sending real messages; replace the implementation details with API calls to your services as needed.
- YAML support requires the optional `PyYAML` dependency. JSON parsing uses the Python standard library.
