[go-Mindustry](https://github.com/tomorrowsetout/go-Mindustry)

<div align="center">
  <a href="https://github.com/MonthZifang/YUEYUEDAO-TECH">
    <img src="./md/logo.png" alt="月月岛科技 Logo" width="720" />
  </a>

  <p><strong>月月岛科技维护 MDT Plugin Market</strong></p>

  <p>
    <a href="https://github.com/MonthZifang/YUEYUEDAO-TECH"><strong>查看月月岛科技详情</strong></a>
  </p>
</div>

# mdt Plugin Market

This repository stores plugin metadata under `src/` and provides a scanner/downloader script.

## Version Rule

- The market version is defined in `market-config.json`.
- A plugin is installable by default only when both `version` and `requiredMarketVersion` match the current market version.
- If someone still wants to install an incompatible plugin, use `--force-install`.

## Structure

```text
src/
  modded/
  native/
scripts/
  plugin_market.py
market-config.json
plugin-market.json
downloads/
```

## Commands

```powershell
python .\scripts\plugin_market.py scan
python .\scripts\plugin_market.py build-index
python .\scripts\plugin_market.py download mdt-jump-plugin
python .\scripts\plugin_market.py --force-install download mdt-jump-plugin
```
