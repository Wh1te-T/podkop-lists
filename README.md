# Списки исключений для Podkop

Российские домены и подсети для секции **Exclusion** в [Podkop](https://github.com/itdoginfo/podkop): эти ресурсы идут напрямую, минуя VPN/Proxy. Списки собираются каждый день через GitHub Actions из [lib4u/amnezia-tunneling-ru](https://github.com/lib4u/amnezia-tunneling-ru), который в свою очередь строится из [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) и [v2fly/geoip](https://github.com/v2fly/geoip).

## Ссылки для Podkop

Домены (поле «Внешние списки доменов»):

```
https://raw.githubusercontent.com/Wh1te-T/podkop-lists/main/lists/russia_domains.srs
```

Подсети (поле «Внешние списки подсетей», по желанию):

```
https://raw.githubusercontent.com/Wh1te-T/podkop-lists/main/lists/russia_subnets.srs
```

Те же списки доступны как `.json` (исходник sing-box rule-set) и `.lst` (простой текст) в папке `lists/`.

## Что делает сборка

Из исходного списка выбрасываются служебные зоны (`*.arpa`, `local`, `lan`, `localhost` и т.п.) и адреса роутеров, поддомены схлопываются в родительский домен, а из подсетей убираются одиночные зарубежные IP (CloudFront, Cloudflare, `1.1.1.1`): это общие адреса, и их исключение пустило бы мимо VPN чужие сайты.

## Ручные правки

Файлы в `custom/` применяются при каждой сборке: `include_domains.lst` и `include_subnets.lst` добавляют записи, `exclude_domains.lst` и `exclude_subnets.lst` убирают. После пуша правок списки пересобираются автоматически.
