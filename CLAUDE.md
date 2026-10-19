# 確率人生

統計ベースの人生シミュレーションゲーム。実行時にLLMは使わない。
LLMは「事前のコンテンツ大量生成」にだけ使い、生成物は data/*.json に置く。

## 構成
- SPEC.md … コンテンツ生成仕様（スキーマ・数値幅・禁止領域・虹ルート）。コンテンツに関わる作業では必ず読む
- data/*.json … 生成済みコンテンツ（分岐・毎年イベント・虹ルート）
- validate.py … 生成物の検品。`python3 validate.py data/*.json` がエラー0であること
- template.html + build.py … 現行デモ。`python3 build.py` で dist/ に1枚のHTMLを出力
- reference/kakuritsu-jinsei.html … 現行デモの完成形（挙動の見本）
- tools/list_topics.py … 既存の id・題材をカテゴリ別・年齢順に一覧（`python3 tools/list_topics.py teen` で絞り込み）
- tools/sim.py … バランス確認。`python3 tools/sim.py --seed 1` で2000人生を random（ランダムに選ぶ）と smart（考えて選ぶ）の2方針で回して表で比較（`--unused` で未出現の分岐、`--template` で別の template.html と比較）

## モデルの役割分担
- メインセッション（Opus）：設計、エンジン、アプリ化、レビュー、バランス調整
- content-writer サブエージェント（Sonnet）：SPEC.md に沿ったコンテンツ生成のみ
- content-reviewer サブエージェント（Opus）：生成物の品質・矛盾チェック
- メインセッションは data/*.json を手で大量に書かない。量産は必ず content-writer に任せる

## ルール
- data/ のJSONを変更したら validate.py を通す
- id は全ファイルで一意。追加生成の前に既存のidと題材を確認する
- 犯罪ルート、性的内容、自殺・自傷・摂食障害、未成年の恋愛は書かない（詳細は SPEC.md）