# Tarantool project HUD

This service shows a lot of useful information in one place as a set of cards.

Currently supported:

- Top downloads from [packagecloud](https://packagecloud.io)
- Builds from [Travis.ci](https://travis-ci.org)
- Builds from [Concourse.ci](https://concourse.ci)

## Quickstart

Create a file named `config.yml` with the following content:

``` yaml
---
concourse:
  url: 'http://build.tarantool.org'
  username: 'your-username'
  password: 'your-password'

travis:
  token: 'your-travis-token'
  user: 'your-travis-user'

packagecloud:
  token: 'your-packagecloud-token'
```

``` bash
docker build -t hud .

docker run --rm -t -i -p 8080:8080 -v $(pwd)/config.yml:/hud/config.yml hud /hud/hud.py -c /hud/config.yml
```

Then point your browser to [localhost:8080](http://localhost:8080)
