# POSTER LAB 海报参考库检索标签标准 v0.2

初稿日期：2026-11-07。本版更新：2026-11-08。状态：已用于 300 条参考案例复核与 12 组书籍视觉意图检索试验；仍是本库受控词表，不是通用设计史分类。枚举 ID 保持 v0.2，新增复核证据字段为兼容扩展。

本标准针对 Codex 中的书籍海报参考检索，自定义一套可维护的受控词表，不宣称是设计行业通用分类。基本词义见同目录 GLOSSARY.md。

本次新增：艺术史与设计史标签 art_history，与视觉路线并列检索。取代 v0.1 作为当前工作草案；旧稿留存。

## 1. 分类原则与数据层次

保留四层信息：来源事实、画面特征、设计解释、具体项目的选例记录。

- 来源事实回答原作是什么，例如音乐会海报、电影海报、创作者与年份。使用独立元数据字段。
- 画面特征回答作品如何呈现，例如字形主导、不对称构图、高文字密度。依据具体图像标注。
- 设计解释回答可以迁移什么，例如秩序、冲突。属于解释，需说明理由。
- 选例记录回答为什么适合某一本书，保存在该书项目中。选作财经书参考，不把音乐海报改标为财经原作。

分类使用多个并列维度，不建“财经 → 商务 → 蓝色 → 极简”式单一路径。一张海报可以跨多个维度命中。

## 2. 命名与记录约定

- 字段名和标签 ID 使用小写英文 snake_case，显示名称使用统一中文。
- 中文名称可调整，稳定 ID 不因改名改变。历史流派与设计师姓名不能作为视觉路线的别名自动替换。
- 单选未知用 null；多选无可靠标签用空数组，并在标注状态中区分待标与已复核。不得以“无”“其他”掩盖不确定性。
- 每条案例记录 taxonomy_version，例如 0.2。词表尚未覆盖的表达写入候选词说明，避免直接写入不存在的枚举值。
- 核心字段须经过一次标注；不确定时允许为空并标为 needs_review。某个字段不确定，不自动剔除整个有效案例。
- 补充字段按需标注。未标注与负面判断是两回事。
- 一次标注记录标注者、日期、所看图片版本、状态 draft（初标）/ needs_review（存在待解决分歧）/ reviewed（已复核）及简短理由。reviewed 指字段与图像经过复核，不表示审美或适配得到用户认可。

## 3. 核心七个维度

| 字段 | 目的 | 数量 | 数据性质 |
|---|---|---|---|
| art_history | 艺术史／设计史脉络与流派名称 | 可多选，通常 1–3；不强行填满 | 有出处的关系或明确标注的视觉判断 |
| visual_family | 整体视觉路线，用于初筛与多样性 | 主路线 1，辅路线最多 1 | 画面分析 |
| visual_driver | 主要靠什么吸引视线和传达信息 | 单选 | 画面分析 |
| composition | 元素如何组织 | 1–3；不确定可空 | 画面特征 |
| text_density | 原作文字信息量 | 单选 | 画面特征 |
| tone | 画面带来的表达气质 | 1–2；证据不足可空 | 设计解释 |
| transferable_concepts | 可跨题材迁移的表达能力 | 0–3，每项附依据 | 设计解释 |

标签数量是本库控制噪声的标注上限，不是制作海报的设计限制。不能为凑足数量添加标签。

### 3.0 art_history：艺术史与设计史标签

本字段支持用户直接查询“瑞士国际主义”“未来主义”“包豪斯”等名称。视觉路线继续回答画面如何工作，两者并存。同一历史传统中存在不同视觉方法；相似视觉方法也可以出现在不同历史背景中。

#### 类型与范围

词表每个条目保存 ID、标准中文名、原文名、别名、类型、简短定义、易混淆项及定义来源。类型使用 movement（运动／流派）、school（学校及其设计传统）、design_style（设计风格）、umbrella（较宽泛的历史思潮）；有需要再增加 regional_tradition（地域设计传统）。这些类型用于避免把学校、运动、年代和地域混为一谈，不形成强制的艺术史谱系树。

本轮的 16 个起步条目如下。视觉线索供检索与读图判断使用，不能独自证明历史归属。英文别名中的大小写不影响查询，中文同义词以明确清单归一。

| 稳定 ID | 标准名称／原文名 | 类型 | 检索线索与边界 | 定义来源 |
|---|---|---|---|---|
| swiss_international | 国际主义平面设计风格／International Typographic Style | design_style | 网格、无衬线、理性编排；别名瑞士国际主义、瑞士风格、国际字体风格、Swiss Style；限定平面设计语境 | [瑞士国家图书馆](https://www.nb.admin.ch/en/the-international-style-1950-1970) |
| futurism | 未来主义／Futurism | movement | 运动、速度、碎裂与现代机器经验；泛指未来感的 futuristic 不作同义词 | [MoMA](https://www.moma.org/collection/terms/futurism) |
| constructivism | 构成主义／Constructivism | movement | 几何建构及艺术服务社会的历史背景；红黑配色或斜线本身不足以归属；“建构主义”仅在艺术语境作别名 | [MoMA](https://www.moma.org/collection/terms/constructivism) |
| bauhaus | 包豪斯／Bauhaus | school | 学校、教学实践与设计传统；不是凡有圆方三角就属于包豪斯 | [MoMA 术语表](https://www.moma.org/momaorg/shared/flattened_pages/moma_learning/glossary/) |
| de_stijl | 风格派／De Stijl | movement | 直线、矩形与原色关系；“新造型主义”作为相关概念扩展查询，不默认为完全同义 | [MoMA 术语表](https://www.moma.org/momaorg/shared/flattened_pages/moma_learning/glossary/) |
| new_typography | 新字体排印／The New Typography | design_style | 不对称排字与信息组织；别名新字体运动、Die Neue Typographie；与新浪潮分开 | [MoMA 专题展](https://www.moma.org/calendar/exhibitions/1013) |
| art_nouveau | 新艺术运动／Art Nouveau | movement | 有机曲线、自然形态与装饰；Jugendstil 等地域变体作为相关词保留，不抹平差异 | [V&A](https://www.vam.ac.uk/collections/art-nouveau) |
| art_deco | 装饰艺术／Art Deco | design_style | 几何化装饰与多种历史、现代来源结合；不同于新艺术运动 | [V&A](https://www.vam.ac.uk/articles/an-introduction-to-art-deco) |
| dada | 达达主义／Dada | movement | 偶然、反逻辑、反讽与拼贴实验；有拼贴不自动属于达达 | [MoMA 术语表](https://www.moma.org/momaorg/shared/flattened_pages/moma_learning/glossary/) |
| surrealism | 超现实主义／Surrealism | movement | 梦境、潜意识与异质关系；与仅描述画面手法的 surreal_concept 分开 | [MoMA 术语表](https://www.moma.org/momaorg/shared/flattened_pages/moma_learning/glossary/) |
| cubism | 立体主义／Cubism | movement | 分解形体、多个视点与压缩空间；三维渲染或普通几何图不算 | [MoMA](https://www.moma.org/collection/terms/cubism) |
| pop_art | 波普艺术／Pop Art | movement | 大众媒介、商品与流行图像；鲜艳配色本身不足以归属 | [MoMA](https://www.moma.org/collection/terms/pop-art) |
| psychedelic_graphics | 迷幻平面风格／Psychedelic Graphics | design_style | 曲线、色彩与感知变化的视觉表达；本词条的初始图像锚点是 Dylan，不据一例概括全部作品 | [MoMA：Dylan](https://www.moma.org/collection/works/8108) |
| new_wave_graphics | 新浪潮平面设计／New Wave Graphic Design | design_style | 非常规字距、字形混用与表达性编排；限定平面设计，不自动等同新浪潮电影或音乐类别 | [MoMA：Public Theater](https://www.moma.org/collection/works/8840) |
| postmodern_graphics | 后现代主义平面设计／Postmodern Graphic Design | umbrella | 引用、杂糅、复杂与矛盾；是较宽类别，优先保留有来源的具体标签 | [V&A](https://www.vam.ac.uk/articles/what-is-postmodernism) |
| plakatstil | 德国海报风格／Plakatstil | design_style | 概括图像与醒目文字构成直接传播；Sachplakat 作为密切相关的物体海报类型，查询可扩展但不直接合并 ID | [Smithsonian](https://www.americanhistory.si.edu/explore/stories/emergence-modernism-early-20th-century-american-advertising-lucian-bernhard-and-his) |

这里只登记与当前海报库相关的起步条目，不声称完整。工艺美术运动、表现主义、至上主义、欧普艺术、朋克图形、波兰海报学派等可随首批案例扩充；每次新增需补独立定义和作品依据。年代和地域在元数据中保存，不能仅凭国籍或年份自动赋予流派。

#### 作品与标签的关系

每个作品标签均须带 relation：

| 值 | 显示名称 | 证据要求 |
|---|---|---|
| historical_affiliation | 历史归属 | 馆藏、设计者、基金会或可信研究明确把作品置于该历史脉络。作者背景可佐证，但不能把作者全部作品批量继承标签 |
| documented_influence | 有据影响 | 来源明确说明作品受到该流派或传统影响，不因此声称作品属于原始运动 |
| visual_affinity | 视觉近似 | 标注者根据原图作出的相似性判断，附可观察理由；不把相似写成影响的事实 |
| revival | 当代复兴／致敬 | 作品或项目来源明确说明复兴、借用或致敬；只有外观相似时用 visual_affinity |

涉及历史或影响事实主张的三种关系 historical_affiliation、documented_influence、revival 必须有 source_url 与 evidence_note，注明证据针对作品还是创作者背景。visual_affinity 用 visual_reason，来源可辅助，但不伪称外部认证。对有争议的归属保留并列证据与 needs_review，不以模型给出的百分比代替出处。

同一 term_id 在一个案例中保存最明确的关系，并保留其他依据；不重复贴多个同名标签来提高检索权重。多个不同流派可以并存。无法判断时保留空列表，表示未确定，不表示没有历史关联。

#### 规范名称消歧

- 瑞士国际主义、瑞士风格、国际字体风格、International Typographic Style、Swiss Style，在明确平面设计语境时归一为 swiss_international。
- International Style 单独出现时有建筑与平面设计歧义，需结合上下文；Swiss design 泛指瑞士设计时也不直接映射。
- Futurism／未来主义是历史术语；futuristic／未来感不是它的自动别名。
- Bauhaus（学校传统）、Constructivism（运动）、geometric_order（视觉路线）可有关联，不能互相替换。
- 新字体排印与新浪潮平面设计分开；二者并非同一标签的中英译法。
- 风格派与新造型主义、新艺术运动与地域变体、Plakatstil 与 Sachplakat 使用相关词扩展，不压成一个无差别标签。

#### 加入检索与展示

用户指定流派时，先规范名称，再按关系分组返回：有来源的历史案例、有据影响或致敬案例、视觉近似候选。明确要求历史原作时，visual_affinity 不能充数；只要求相近视觉风格时，可以加入并清楚标注。

用户未指定流派时，以内容和视觉方法选例，并使用 art_history 检查参考范围是否过于集中。仍至少展示 4 张真实海报，优先不同视觉路线与历史脉络；不要求每张都来自一个互斥流派。

每张参考的说明可展示“流派／设计史标签＋关系＋视觉路线＋为何适合本书”。普通观众可先看中文名称，来源细节放案例卡。

#### 具体试标

- Public Theater 95–96：可将 new_wave_graphics 与 historical_affiliation 配对，证据是 [MoMA 对这张作品的说明](https://www.moma.org/collection/works/8840)，其中将其编排与新浪潮设计者的实践联系起来。原有 expressive_type 仍保留。
- Dylan：可将 psychedelic_graphics 与 historical_affiliation 配对，证据是 [MoMA 对这张作品的说明](https://www.moma.org/collection/works/8108)。这里表示置于迷幻视觉语境，不宣称作者加入了某个正式组织。原有 illustrative_organic 仍保留。
- Beethoven：swiss_international 有 [设计师基金会的背景与作品研究](https://syjmb.foundation/en/josef-mueller-brockmann/)及瑞士风格资料支持。当前案例仅保留 visual_affinity；本轮没有取得足以升级为作品级历史归属的证据，不能用“瑞士人”替代作品判断。geometric_order 的画面标注不受影响。
- The Man with the Golden Arm：本轮来源已核验作品身份，但不强行为它指定尚未核验的具体历史流派。symbolic_reduction 标签可正常检索。

数据片段示例：

```yaml
art_history:
  - term_id: new_wave_graphics
    relation: historical_affiliation
    source_url: https://www.moma.org/collection/works/8840
    evidence_scope: work
    evidence_note: 馆藏说明将该作的设计方法与新浪潮平面设计实践联系起来。
```

词表应同时校验 term_id、relation、证据字段及版本。历史作品、当代致敬和模型相似性判断不得在展示中混为一种状态。

### 3.1 visual_family：视觉路线

| ID | 标准名称 | 判定要点 | 区分边界 |
|---|---|---|---|
| geometric_order | 几何秩序 | 重复、比例或几何关系构成主要视觉逻辑 | 仅有方形版框不足以成立 |
| expressive_type | 表现性字体 | 字形尺度、方向、变形或排列承担表达 | 标题很大但常规排列，不自动成立 |
| symbolic_reduction | 符号凝练 | 一个或少量概括图形承载核心概念 | 普通装饰图标不是核心符号 |
| illustrative_organic | 有机插画 | 手绘感、曲线与有机形态主导表达 | 拍摄植物的照片不因此归入此类 |
| photographic_editorial | 摄影叙事 | 照片主体、情境与编辑编排共同传达主题 | 角落的小照片不构成此路线 |
| collage_montage | 拼贴蒙太奇 | 多个不同来源感的片段经组合产生意义 | 单个人物抠图不自动等于拼贴 |
| surreal_concept | 超现实观念 | 不可能的比例、组合或空间制造隐喻 | 普通抽象图形不等于超现实 |
| ornamental_pattern | 装饰纹样 | 纹样、边饰或装饰系统形成整体身份 | 小面积花边不构成主路线 |
| diagrammatic_information | 图解信息 | 地图、关系、流程或数据组织成为主视觉 | 看起来像图表但无关系表达的图形不算 |
| material_experiment | 材质实验 | 纸张、油墨、撕裂、印痕等质感成为表达主体 | 做旧滤镜或印刷痕迹不自动成立 |

主路线按“去掉哪种方法，作品最主要的表达会消失”判定。辅路线只在另一方法同样明显时使用。拟扩展的赛博、复古等词须先拆解可观察特征，不能凭感觉建大筐。

这些是检索类别，不是互斥的艺术史标签。例如同一作品可能是 symbolic_reduction 主路线、geometric_order 辅路线；四张参考的差异还需看主体、构图与技法。

### 3.2 visual_driver：视觉主体

| ID | 标准名称 | 判定要点 |
|---|---|---|
| type | 字体主导 | 字形本身是主要视觉主体，不只作为图像说明 |
| image | 图像主导 | 摄影或具象插画承担主要表达 |
| symbol | 符号主导 | 抽象几何或概括图形承担主要表达 |
| diagram | 图解主导 | 关系、路径、流程或数值组织承担主要表达 |
| balanced | 图文并重 | 图与字相互作用，去掉任一方都会显著削弱画面 |

按表达作用判断，不机械按像素面积计算。大标题与人物共同构成海报，可以是 balanced。

### 3.3 composition：构图组织

| ID | 标准名称 | 判定要点 |
|---|---|---|
| centered | 中心聚焦 | 主体或信息重心集中在中心区域 |
| asymmetric | 不对称平衡 | 重心偏置，通过留白或其他元素维持平衡 |
| grid | 网格组织 | 信息沿可辨认的行列系统组织 |
| modular | 模块分区 | 明确的块面容纳不同信息或图形 |
| diagonal | 对角动势 | 主要阅读方向或结构沿斜向展开 |
| radial | 放射环绕 | 围绕一个中心展开、旋转或形成同心结构 |
| stacked | 层叠堆积 | 图文纵向堆叠或相互覆盖成为主要结构 |
| split | 分割对照 | 两个或多个明显区域形成并置关系 |
| frame | 框景包围 | 外围元素包围主体或信息区 |
| full_bleed | 满版延伸 | 主图或主图形显著延伸至画面边缘 |
| negative_space | 留白聚焦 | 大块未被信息占据的空间参与构图 |
| repeating_field | 重复铺陈 | 重复单元组成主要视觉场域 |

grid 不等于 geometric_order：摄影排版也可使用网格。modular 不等于 grid：不规则色块也可以模块分区。留白指低信息空间，颜色可以是黑或其他色，不专指白色。

### 3.4 text_density：原作文字密度

| ID | 标准名称 | 判定要点 |
|---|---|---|
| low | 低文字密度 | 通常是题名与少量辅助信息，缺少多组需要阅读的内容 |
| medium | 中文字密度 | 题名之外还有独立说明、节目或署名等可辨识信息组 |
| high | 高文字密度 | 多个独立信息组或连续文字竞争阅读注意力 |

不按文字占画面面积分级，也不固定字数门槛。一个占满画面的词仍可是低密度。长书名并不等于高信息密度。tiny legal credits 不因字符很多自动把电影海报判为 high，考虑实际阅读层级。

### 3.5 tone：表达气质

| ID | 标准名称 | 可援引的画面依据 |
|---|---|---|
| restrained | 克制 | 有限变化、稳定层级与节制的强调 |
| energetic | 活跃 | 高频节奏、方向变化、充满运动感的形态 |
| dramatic | 戏剧性 | 强烈明暗、尺度或构图冲突 |
| playful | 诙谐 | 有意的视觉玩笑、轻盈变形或趣味组合 |
| solemn | 庄重 | 稳定、仪式化、肃穆的视觉组织 |
| intimate | 亲近 | 私人尺度、手写或日常细节带来的亲近感 |
| mysterious | 神秘 | 遮蔽、暗示、不完整信息带来的未知感 |
| rebellious | 反叛 | 刻意打破常规秩序的视觉姿态 |

tone 属于解释，不因题材自动添加。金融题材不自动等于克制，革命主题不自动等于反叛，红色不自动等于活跃。避免高级、好看、大气、国际范等缺少判定边界的词。

### 3.6 transferable_concepts：可迁移概念

每个概念都要能补全“画面中的……可以用于表现……”。无法补全则不标。原作主题出现一个词，不构成画面支持。

| ID | 标准名称 | 结构依据示例 |
|---|---|---|
| order | 秩序 | 重复单元遵循可识别的组织规则 |
| aggregation | 聚合 | 多个部分形成一个整体 |
| dispersion | 分散 | 统一形体拆开、散布或分离 |
| connection | 连接 | 路径、接点或交织关系把元素相连 |
| growth | 生长 | 形态逐步展开、增殖或延伸 |
| conflict | 冲突 | 元素挤压、对撞或形成明显对立 |
| power | 权力 | 统摄、控制或悬殊尺度关系 |
| transformation | 转变 | 形态发生明确转换或穿越边界 |
| time | 时间 | 连续阶段、节律或痕迹组织时间感 |
| memory | 记忆 | 残片、叠影等使过去以痕迹形式出现 |
| identity | 身份 | 轮廓、面孔、标识或角色特征聚焦身份 |
| exploration | 探索 | 路径、入口或逐层揭示构成未知旅程 |
| fragility | 脆弱 | 断裂、悬置、失衡等显示易损状态 |
| cycle | 循环 | 路径闭合、回返或阶段反复 |
| complexity | 复杂性 | 多层结构、交错关系或多重信息共同作用 |
| contrast | 对照 | 两种状态被有意并置以产生意义 |

这些词描述设计表达能力，不声称设计者原意。一个圆不自动表示循环，一张旧图片不自动表示记忆。当前《万亿指数》相关概念也不能全部贴给参考作品。

## 4. 按需补充的四个维度

### 4.1 techniques：具体表现手法，多选 0–3

| ID | 标准名称 | 判定边界 |
|---|---|---|
| silhouette | 剪影 | 以整体轮廓表达主体 |
| cutout | 抠图 | 主体脱离原背景后进入新构图 |
| flat_shapes | 平面色块 | 无明显体积塑造的块面组织 |
| linework | 线描 | 线条承担主要造型 |
| geometric_repeat | 几何重复 | 几何元素的重复关系明显 |
| organic_curves | 有机曲线 | 自由曲线组织形态 |
| photomontage | 摄影拼合 | 多个摄影片段的组合产生新画面 |
| paper_collage | 纸片拼贴 | 纸片的切割、撕边或叠放可辨认 |
| overprint | 叠印效果 | 色层相交产生叠合视觉；不据此断言印刷工艺 |
| halftone | 网点效果 | 可辨识网点成为画面表现 |
| texture | 材质纹理 | 纹理明显参与表达 |
| spatial_illusion | 空间错觉 | 不寻常或不可能的空间关系 |

图像看起来像剪纸不表示它确由剪纸制作。事实中的印刷媒介仍以来源记录为准。

### 4.2 typography：文字处理，多选 0–3

| ID | 标准名称 | 判定要点 |
|---|---|---|
| neutral_typesetting | 中性排字 | 常规字形、明确层级，文字处理不主动抢占表达 |
| oversized | 超大字形 | 字形尺度本身成为视觉事件 |
| condensed | 窄体字形 | 明显压窄或使用窄体字形 |
| multidirectional | 多向排字 | 多种阅读方向共同构成画面 |
| hand_lettered | 手写字形 | 明显的手写、手绘字形特征 |
| custom_display | 定制展示字形 | 标题字具有明显特殊造型；不凭图像断言定制制作过程 |
| integrated | 图文融合 | 图形与字形相互嵌入或共用轮廓 |
| vertical_setting | 竖向编排 | 文字有意按竖向阅读或排列 |

不从低清晰度图像猜测具体字体名称。中文字体可用性、字体授权另行验证。

### 4.3 color：色彩组织

color_mode 单选：achromatic（黑白灰主导）；limited_palette（少量主色形成清楚关系）；multicolor（多种颜色共同承担表达）；photographic（照片连续色调主导）。无需数出严格色数边界，纸张泛黄与扫描噪声不算设计用色。

color_contrast 单选：strong（主要信息区域明暗或色彩对比强）；soft（主要关系柔和）；mixed（强弱对比明显并存）。不确定留空。

主要色名作为辅助字段 dominant_colors，最多 3 项，从 black、white、gray、red、orange、yellow、green、blue、purple、pink、brown 中选。扫描色偏较大时备注，不能把色名当主题或风格的替代。

### 4.4 adaptation：书籍海报适配

这是条件判断，不混进原作观察标签。

评估维度：long_title（长书名）、han_typesetting（汉字编排）、dense_copy（多组文案）。每项取 low_rework（主要结构可保留）、medium_rework（需要调整局部区域或文字处理）、high_rework（需要改变核心结构）、unknown（尚未评估）。这是允许显式 unknown 的评估字段，与观察字段的 null 区分。每项有判断时附一条理由。

另记 basis：inferred（由原作推断）或 tested（有实际试制文件支持）。tested 必须能定位到对应试制记录。不能只根据原作语言断定汉字难以适配；英文单字紧缩排版往往更需要重排，但仍应看具体结构。

新增案例可暂不填写 adaptation；正式为一本书选例时再结合其实际标题和文案判断。

## 5. 来源元数据与题材

原始用途 original_use 使用 book_promotion（书籍推广）、exhibition（展览）、performance（演出）、film（电影）、music_release（音乐发行）、event（其他活动）、commercial（商业宣传）、public_message（公共传播）、other（已知但暂不覆盖，需说明）；未知用 null。用途核验尽量依据出处，无法核验时单独标为推测。

原始题材 original_subjects 暂作为保留来源用词的短文本，例如音乐、剧场、电影。书籍的历史、金融、文学等题材记录在书籍任务中，初期不为所有学科另建庞大枚举。待反复出现实际检索需求时，再形成独立题材词表。

尺寸、比例、语言、版本、图片路径、来源、权利状态、是否能显示属于元数据；不混入设计标签。扫描图边框不应直接作为海报尺寸测量依据。

“可参考”与“素材可直接复用”是两个判断。来源不明或权利未知的素材不能因此标成可自由复用；参考检索本身不按成品素材授权直接排除所有案例。

## 6. 同义词归一与模糊词处理

| 输入词 | 处理方式 |
|---|---|
| 大字报、强字体、字形表达 | 检查是否符合 expressive_type；不是无条件自动映射 |
| 拼贴、蒙太奇 | 查询扩展到 collage_montage；再检查是否只有单个抠图 |
| 几何、网格、瑞士风 | 几何与网格分别检查 geometric_order、grid；瑞士风在平面语境查询 art_history 中的 swiss_international，并显示作品关系与证据 |
| 极简、简约 | 根据实际情况检查 symbolic_reduction、negative_space、restrained、low；不一键套全 |
| 复古 | 查询可包含历史年份、材质、字体与色彩特征；不设单一正式标签 |
| 高级、大气、有设计感 | 保留为用户审美要求，转换成具体可讨论特征，不写入正式词表 |
| 红黑、蓝白 | 拆成主色与对比字段，不写成风格 |
| 财经、历史、文学 | 作为任务题材或原作题材，不能映射为固定风格 |

同义词表承担查询理解，不把相近但不等价的视觉概念强行合并。所有自动映射均可被图像证据纠正。

## 7. 四张原作的试标

以下为基于已查看图片的首次试标，不声称艺术史定论或已完成跨标注者一致性验证。此处 P 编号沿用拟定案例编号，正式库仍未创建。

| 案例 | 主视觉路线 | 视觉主体 | 构图 | 文字密度 | 气质 | 可迁移概念 |
|---|---|---|---|---|---|---|
| P-0001 Beethoven | geometric_order | symbol | radial, asymmetric, negative_space | medium | restrained | order, time |
| P-0002 Public Theater 95–96 | expressive_type | balanced | modular, stacked, full_bleed | high | energetic, rebellious | conflict, complexity |
| P-0003 The Man with the Golden Arm | symbolic_reduction | symbol | modular, centered, frame | medium | dramatic | fragility, conflict |
| P-0004 Dylan | illustrative_organic | image | full_bleed, negative_space | low | energetic | identity, complexity |

解释依据：

- P-0001：弧线的比例与重复支撑秩序；间隔与节奏可迁移为时间表达。时间属于解释，若后续标注者认为依据不足可以移除，不影响几何路线。
- P-0002：大字与人物共同建立主体；多向、不同尺度字形挤压出冲突，多组信息构成复杂性。模块组织优先于机械认定统一网格。
- P-0003：不自然弯折的手臂轮廓支持脆弱与张力解释；块面包围信息区。不能因为片名有 Golden 就把金色列为主色。
- P-0004：具象人物轮廓承担身份表达，有机多色曲线支持复杂性；不能仅因题材是音乐就添加音乐节适配标签。

四张均应保留各自来源记录，详见本目录《Trillions-首轮研究与方向.md》。这里不重新将来源事实混入分析标签。

## 8. 记录示例与存储约定

2026-11-08 建库时确定：每个案例的 `case.json` 是唯一可编辑数据源，包含元数据、标签、依据和分析；`case.md` 是脚本生成的阅读卡片。`index.jsonl`、`gallery.html`、`coverage.json` 也从案例 JSON 重建，不手工修改生成物。初版使用 Python 标准库，不依赖 YAML 解析器。下方 YAML 仅用于紧凑展示字段结构，不是实际存储格式。

```yaml
id: P-0001
taxonomy_version: '0.2'
annotation_status: draft
observed:
  visual_family:
    primary: geometric_order
    secondary: null
  visual_driver: symbol
  composition: [radial, asymmetric, negative_space]
  text_density: medium
interpreted:
  tone: [restrained]
  transferable_concepts:
    - id: order
      reason: 弧线的比例与重复形成可识别的组织规则。
    - id: time
      reason: 间隔与节奏可以迁移为时间表达；属于初步解释。
```

这是字段片段，不是完整案例模板；来源和图像等元数据另有字段。索引保存作品基本信息、路径、状态和核心检索维度；CLI 检索读取完整案例以支持其他维度。详细记录始终以案例 JSON 为准。

## 9. 检索规则

1. 从书籍资料和用户用途得到主题、核心矛盾、标题和文案约束。未说明的偏好不冒充用户要求。
2. 将内容转为若干可能的视觉概念。例如《万亿指数》可检索 order / aggregation，以及 transformation / power / conflict 两组不同切口。
3. 各组标签作候选扩展，不能要求案例命中全部概念。跨题材检索正常保留音乐、电影等来源。
4. 查看候选原图与解释，评估实际内容联系。标签命中只产生候选，不代替读图和判断。
5. 选至少 4 张真实海报供用户看，优先使主视觉路线不同。若有同路线案例，需能说明其主体、构图或技法上的实质差异。风格多样性服务于书籍表达，不为填四个类别而塞入无关作品。
6. 文字密度、原作语言和色彩优先作为适配提示；只有用户明确指定且不可改变的要求才用于严格过滤。不能因原图是英文就过滤掉中文项目参考。
7. 若候选不足，先放宽非必要的色彩、气质等条件，再补充检索；明确说明不足，不编造标签或案例。

不在初版设未经评估的固定分数权重。选择记录须解释内容联系、视觉方法、适配代价和差异性；解释比伪精确的总分更有用。

## 10. 标注与维护验收

先用四张案例校准，再扩大到约 12 张差异明显的案例，补入摄影、拼贴、装饰与信息图解等尚未覆盖的类型。不要据四个案例就宣称完整词表已验证。

一次标注流程：核对图像版本 → 记录来源事实 → 标核心七维（历史关系不明确时保留空值）→ 为解释字段写依据 → 按任务补充适配 → 检查是否有矛盾、过度贴标或重复词。

用相同图像做一次独立复标，不向复标者透露先前标签。记录逐维分歧及原因，重点看主视觉路线、密度与迁移概念。遇到分歧先修定义或保留不确定性，不能仅靠强制选一个标签掩盖问题。

完成结构化入库时的机械检查：ID 和路径有效；所有值在词表内；单多选数量合法；解释概念有理由；tested 适配有试制记录；没有用自由拼写产生重复枚举；未知不被写成已验证结论。视觉判断还需人工或模型读图复核。

新增标签应证明它区别于已有词、能改变实际检索结果，并附正例和易混淆反例。候选词先写在候选区，经复核后更新词表版本。废弃标签保留迁移映射，不直接删除历史含义。用户反馈与风格偏好保留在项目评价中，不自动变成普遍标签。

## 11. 当前交付边界

本标准起于四图试标，2026-11-08 已用于首批本地参考库。库内提供来源记录、结构化初标、离线浏览、检索和机械校验工具；实际数量及覆盖缺口以 `coverage.json` 为准。Python 校验不等于完整 JSON Schema，抽查也不等于逐张完成独立复标。标注状态须保留，尚未完成面向任意书籍的自动选图评估或完整 Skill 发布。



## 300 条扩充后的执行补充

检索操作和判定边界见 [RETRIEVAL-GUIDE.md](RETRIEVAL-GUIDE.md)。四层信息继续分开，未改变既有 ID。

reviewed 记录新增 review 对象：reviewer、reviewed_at（有效 ISO 日期）、image_sha256、source_check、visual_check、source_urls。验证器以本地预览图重新计算哈希；仅改状态无法通过。原始来源记录或旧库审计摘要保存在每条 source-record.json，来源记录哈希也保存在 review 中。

全库覆盖十条主视觉路线；流派覆盖见 coverage.json，当前 de_stijl 仍为空。不能为了填平统计而强贴流派。复核不意味着每条作品均有已知作者/精确年份，来源不明处继续保留 null 或原文的约略日期。
