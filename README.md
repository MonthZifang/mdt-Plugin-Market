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

这个仓库是纯 Git 协议插件市场仓库。

它不负责执行下载脚本，也不负责生成索引文件。

它只负责：

- 通过 Git 提供市场目录
- 通过固定路径提供市场配置
- 通过固定路径登记插件仓库
- 通过固定文件名让客户端统一识别插件元数据

## 固定协议

客户端统一按以下步骤工作：

1. `git clone` 或 `git pull` 本仓库
2. 读取根目录 [market.json](C:/Users/43551/Desktop/serve-mdt/go-mdt-Plugin-Market/market.json)
3. 根据 `scanDirectories` 扫描 `src/modded` 和 `src/native`
4. 读取这些目录下全部 `*.repo.json`
5. 每个 `*.repo.json` 只负责登记一个插件 Git 仓库
6. 客户端拉取对应插件仓库
7. 客户端在插件仓库固定读取 `market.plugin.json`
8. 再根据 `market.plugin.json` 里的 `downloadUrls`、`dependencies`、`entry` 等信息完成展示、校验和下载

## 版本规则

市场当前版本由 `market.json` 中的 `version` 控制。

默认安装规则：

- 插件 `version` 必须等于市场 `version`
- 插件 `requiredMarketVersion` 必须等于市场 `version`

如果客户端支持强制安装，可以在版本不一致时跳过这个校验。

## 目录结构

```text
market.json
src/
  modded/
    *.repo.json
  native/
    *.repo.json
md/
  logo.png
```

## 根配置文件

`market.json` 是市场固定入口文件。

主要字段：

- `name`
- `version`
- `mode`
- `pluginMetadataFile`
- `registryFileSuffix`
- `scanDirectories`
- `installRule`

## 仓库登记文件

`src/modded/*.repo.json` 和 `src/native/*.repo.json` 是插件仓库登记文件。

推荐字段：

- `name`
- `displayName`
- `author`
- `channel`
- `targets`
- `gitRepository`
- `gitBranch`
- `pluginMetadataFile`

## 插件仓库固定识别文件

插件仓库必须在固定路径提供：

```text
market.plugin.json
```

客户端统一扫描这个文件识别插件信息。

## 说明

- 这个仓库不生成本地索引
- 市场逻辑全权交由 Git 路径与固定元数据文件完成
- 如果你想提交你自己的插件请提交PR

 ## 插件提交必要说明

- 插件原则上应开源。非开源插件也可以接入本仓库，但必须提供完整的插件源码或 JAR 文件。
- 如果你的插件是其他插件的衍生作品，必须遵守原作者发布的个人协议，并受该协议约束。
- 如有任何问题，请通过提交 Issue / 提议，或邮件、QQ 群等渠道与我联系。
 
