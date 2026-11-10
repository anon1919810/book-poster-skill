# 公开发布与图片授权

完整研究图库与公开起步库分开维护。`case.json` 仍是案例、来源与视觉标注的依据；`rights/release-manifest.json` 单独保存发布决定，两者通过文件 SHA-256 关联。

| image_status | 含义 | 图片可被导出 |
| --- | --- | --- |
| unreviewed | 尚无足够的再分发依据 | 否 |
| candidate | 有公共领域或许可线索，尚未完成复核 | 否 |
| approved | 对当前图片与案例记录完成证据核对 | 是 |
| excluded | 已明确决定不进入公开包；在 notes 记录原因 | 否 |

`annotation_status=reviewed` 只表示原有的来源与图像标注复核。`No known restrictions` 只是继续核查的线索，不自动等于公共领域或许可。缩略图、拼图和浏览页中的内嵌图片同样需要处理；改为公开服务器图片地址不替代授权。

每个批准记录必须有：图片与案例哈希、许可/公共领域依据 `basis`、证据链接、经过筛选的本地 JSON 证据及其哈希、复核日期、复核者、署名内容、是否必须署名、适用范围与限制说明。`approved` 是项目的有据发布决定，不是任何地区、任何用途均无第三方权利的保证。

## 使用

在仓库根目录运行（Python 3.10+）：

```sh
python -X utf8 library/tools/release.py init --root library
python -X utf8 library/tools/release.py audit --root library
python -X utf8 library/tools/release.py export --repo . --dest ../book-poster-public-candidate
```

`init` 只在尚无清单时运行，不能覆盖人工复核。它只根据旧备注生成候选，不批准图片。修订清单后运行 `audit`；图片或案例内容变化会使旧证据绑定失效，需要重新核对。证据中的路径相对 library，放在 `rights/evidence/*.json`；不要放密钥、个人路径、整页转载或无关原始响应。

`export` 只向库外全新目录写文件，拒绝覆盖、路径穿越、符号链接与 Windows junction。采用明确白名单：Skill、工具、分类文档、批准案例和批准图片；索引、案例页、图库页重新生成。失败时目录可能留下未完成候选，请检查报错并选新目录重试，不把失败目录发布。

完整 300 条的公开目录只保留作品身份、来源作品页和受控标签；无授权图片的记录只显示来源链接，不包含图片下载地址、原始分析和证据长文。`library/gallery.html` 仅展示实际附带的图片；`catalog.html` 与 `catalog.json` 包含来源目录。缺图记录不能当作已经看过、展示过或可取图的参考。

公开起步库需要风格覆盖说明，不能把历史海报子集描述为原私有库的等价替代。用户可配置自己的 `library_root`，也可在任务中另行检索真实参考。许可证只涵盖各自指定的内容，代码的许可证不为图片重新授权。

## 发布前

- 检查 `release-report.json` 的文件清单、校验结果与图片范围，以及 `CREDITS.md`。
- 自有代码、Skill 文档与原创分析已选用 MIT；保留根目录 LICENSE 与 LICENSE-SCOPE.md。图片与第三方数据遵循各自来源条款，不因代码采用 MIT 而重新授权。
- 在候选目录建立全新的 Git 仓库，不携带完整研究库的历史。不要直接切换原仓库可见性。
- 网站、生成作品、个人路径、使用账本、服务配置、缓存和历史验收记录不进入公开包。

工具只负责审计和本地导出，不创建远程仓库、不提交、不推送，也不修改原始图片或案例。
