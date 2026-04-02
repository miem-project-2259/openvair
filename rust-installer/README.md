# Установка

```shell
$ cargo install --path <ПУТЬ ДО ЭТОЙ ДИРЕКТОРИИ>
```

# Usage

```shell
openvair-manager install -u aero
```

# Testing

```shell
cargo test
```

## Testing for a specific distribution example

Different distributions should be hidden by the corresponding
feature flag. If you with to test some code for a particular
distribution -- run the test as so

```shell
cargo test -f ubuntu
```
