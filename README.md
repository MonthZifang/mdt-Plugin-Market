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

# mdt 插件市场

这是一个通过 `git clone` / `git pull` 获取插件列表的插件市场仓库。

## 版本规则

- 当前市场版本由 `market-config.json` 中的 `marketVersion` 控制。
- 插件默认只有在 `version` 和 `requiredMarketVersion` 都与当前市场版本一致时才允许正常安装。
- 如果用户明确要求安装不匹配版本的插件，可以使用 `--force-install` 强制安装。

## 目录结构

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

## 常用命令

```powershell
python .\scripts\plugin_market.py scan
python .\scripts\plugin_market.py build-index
python .\scripts\plugin_market.py download mdt-jump-plugin
python .\scripts\plugin_market.py --force-install download mdt-jump-plugin
```

## 元数据说明

每个插件使用一个独立的 `*.market.json` 文件描述，支持以下主要字段：

- `name`
- `displayName`
- `author`
- `description`
- `version`
- `requiredMarketVersion`
- `channel`
- `targets`
- `downloadUrls`
- `dependencies`
- `repositoryUrl`
- `entry`

下载链接必须指向完整文件，不能是目录或站点首页。
