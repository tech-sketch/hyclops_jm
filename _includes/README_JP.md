# 概要 {#about}

HyClops JobMonitoringは監視のZabbixとジョブ管理のJobSchedulerを連携させるツールです。
JobSchedulerのジョブ監視をZabbixにて行います。

*※ HyClopsシリーズはJobMonitoring以外に[HyClops for Zabbix](http://tech-sketch.github.io/hyclops/jp/)があります。
HyClops for Zabbixではハイブリッドクラウド環境の監視や簡単な操作をZabbixから実現できるようにしました。*

JobMonitoringでは第2ステップとしてZabbixに不足しているジョブ管理機能に着目し、ジョブ管理ツールとの連携を実現しました。
対象のジョブ管理ツールには高度な機能を持つJobSchedulerにフォーカスし、JobSchedulerとの連携を実現したことで、運用担当者の煩わしい作業を軽減させることが出来ます。

JobMonitoringの特徴はZabbix及びJobScheduler自体の改変はせず、各ツールが持つAPIを活用して連携させていることです。

HyClops JobMonitoringの機能概要:

* ジョブ監視設定をZabbixに自動登録
* ジョブの実行時間をZabbixで監視し、時間推移を取得
* ジョブの異常終了や遅延情報をZabbixに連携し、Zabbixのアクションに基づいた対応を実施
* ジョブの稼働に合わせた自動トリガー設定変更

# リリースノート {#releases}

* 2014/12/xx ver.0.1.0
  * 初期リリース
 
# アーキテクチャ {#architecture}

![architecture]({{ site.production_url }}/assets/images/HyClopsJM_architecture.png)

HyClops JobMonitoringはJobSchedulerとZabbixをAPIにてコントロールしています。
各APIを操作するためのスクリプトとしてFabric形式のスクリプトで構成しています。
また、APIを利用する際に必要なZabbixやJobSchedulerのIPアドレス/ポート番号や認証情報をDBに保有しています。

# 機能詳細

各機能の詳細について説明します。

## ジョブ実行時間の取得

![architecture]({{ site.production_url }}/assets/images/job_elapse_detail.png)

JobMonitoringはJobSchedulerのジョブ定義に従い、Zabbixに自動でジョブの監視アイテムやホストを登録します。その後、自動登録されたアイテムに対して各ジョブ毎の実行時間が定期的に登録されます。Zabbixに登録される情報は以下となります。

| Zabbixへの自動登録情報 | 説明 |
|--------|-----|
| テンプレート | Template App JobScheduler と Template App HyClops JM の2つのテンプレートが自動で登録されます。
| ホスト | JobSchedulerのジョブのprocess_class定義(ジョブ実行先ホスト情報)に従い、Zabbixのホスト情報が設定されます。対象ジョブにprocess_classが定義されていない場合はZabbixへはlocalhostというホストが登録されます。
| アイテム | ジョブ情報を元に各ジョブのアイテムが自動登録されます。各アイテムにはジョブの実行時間が秒で登録されます。

## ジョブ異常状態のZabbix連携

ジョブの異常が発生した場合にJobSchedulerからのメール送信をフックし、Zabbixに対してエラーフラグが連携されます。
これにより、Zabbixにてエラーフラグの状態をトリガーにてハンドリングし、アクション設定にて適切なアクションを実行することが出来ます。

## ジョブの稼働に合わせた自動トリガー設定変更

![architecture]({{ site.production_url }}/assets/images/error_collaboration_detail.png)

特定ジョブが稼働する前後でトリガー変更テンプレートジョブを実行することで指定したトリガーしきい値を変更することが出来ます。
サンプルでは前処理のジョブが失敗しても必ずメインのユーザジョブは稼働するようにJob Chainが設定されています。

# インストール {#install}

## 前提条件

利用可能なOSは以下のOSです。

* CentOS 6(検証済: 6.5)

HyClops JobMonitoringを利用するには1つのインスタンスに以下をインストールする必要があります。

* Zabbix (2.2以上) (検証済: 2.2.7, 2.4.2)
* Python (2.6) (検証済: 2.6.6)
* Fabric (1.10以上) (検証済: 1.10.0)
* PostgreSQL (9.3以上) (検証済: 9.3.5)
* JobScheduler (1.7以上) (検証済: 1.7.4274)

[こちらで用意しているスクリプト](https://github.com/tech-sketch/hyclops_jm-chef-repo)を利用すれば、上記ミドルウェアを一括でインストールすることが出来ます。

なお、各ミドルウェアのインストールを手動で実施する場合は以下のページをご参照下さい

* [Zabbix2.2 インストール手順](https://www.zabbix.com/documentation/2.2/manual/installation/install_from_packages)
* [Fabric インストール手順](http://www.fabfile.org/installing.html)
* [PostgreSQL インストール手順](http://www.postgresql.org/download/linux/redhat/)
* [JobScheduler インストール手順](http://www.sos-berlin.com/doc/en/scheduler_installation.pdf)

## インストール手順

以下の手順はすべてrootユーザで実施する前提となっています。

GithubよりHyClops JobMonitoring一式をダウンロードします。

    安定バージョンをダウンロードしたい場合
    # curl -O https://github.com/tech-sketch/hyclops_jm/archive/[version no.].tar.gz
    # tar zxvf hyclops_jm-[version no.].tar.gz
    最新バージョンをダウンロードしたい場合
    # git clone https://github.com/tech-sketch/hyclops_jm.git

ダウンロードしたパッケージディレクトリに移動し、インストール設定を記述します。

    # cd hyclops_jm
    # vi hyclops_jm.conf

環境に合わせて以下の設定を行います。

    # HyClops JobMonitoring user
    jm_user = hyclops_jm    # HyClops JobMonitoring用OSユーザ
    jm_passwd = hyclops_jm  # 上記ユーザのパスワード

    # JobScheduler configuration
    js_id = scheduler       # JobSchedulerのscheduler id
    js_user = scheduler     # JobSchedulerのインストールユーザ
    js_passwd = scheduler   # 上記ユーザのパスワード
    js_host = 127.0.0.1     # JobSchedulerの実行ホストのIP
    js_port = 4444          # JobSchedulerの待ち受けポート

    # Zabbix configuration
    zbx_host = 127.0.0.1    # Zabbixの実行ホストのIP
    zbx_login_user = Admin  # Zabbix Web UIにログイン可能な管理者ユーザ
    zbx_login_passwd = zabbix   # 上記管理者ユーザのパスワード
    zbx_external_scripts_dir = /usr/lib/zabbix/externalscripts  # Zabbixの外部チェック用スクリプトの格納ディレクトリ

    # Database super user
    db_user = postgres    # PostgreSQLのスーパーユーザ
    db_passwd =           # 上記ユーザのパスワード
    db_host = 127.0.0.1   # PostgreSQL実行ホストのIP
    db_port = 5432        # PostgreSQLの待ち受けポート
    pgsql_version = 9.3   # PostgreSQLのバージョン

Fabricのインストールスクリプトにてインストールを実行します。

※  Fabric実行前に127.0.0.1に対してrootユーザでsshで接続可能な状態として下さい。

    # fab -c hyclops_jm.conf install

上記のスクリプトを実行することでHyClops JobMonitoring用DB作成と関連スクリプト群が指定のディレクトリに配布されます。

# 利用方法 {#usage}

以下の設定をすることで利用可能となります。

## ジョブ実行時間の取得

特に設定は必要ありません。インストールから一定時間経過した後、JobSchedulerのprocess_class設定に従ってジョブの監視アイテムがZabbixに登録されます。
また、JobSchedulerにジョブを登録すると自動でZabbixにジョブの監視アイテムが設定されます。

![host]({{ site.production_url }}/assets/images/zabbix_host.png)

![items]({{ site.production_url }}/assets/images/zabbix_items.png)

## ジョブ異常状態のZabbix連携

ジョブで異常終了や開始終了遅延が発生した場合にprocess_class設定に従って対象のホストに設定されている下記アイテムに「1」が登録されます。

* jos_server_status

このアイテムに対してZabbixのトリガー設定を行うことでジョブの異常監視をZabbixで実施します。

*※  初期リリース時点では [issue#4](https://github.com/tech-sketch/hyclops_jm/issues/4) のためにジョブの異常状態をZabbixに登録されたホスト「localhost」のみに 1 を登録します。*

![latest_data]({{ site.production_url }}/assets/images/zabbix_latest_data.png)

## ジョブの稼働に合わせた自動トリガー設定変更

インストールした時点でJobSchedulerの hyclops_jm ディレクトリ以下にJob Chain: HyClops_JM_Trigger_Switch_Template が登録されています。
このJob Chainが自動トリガー変更のテンプレートとなっており、これを利用することで自動トリガー設定変更が可能となります。

![template_jobchain]({{ site.production_url }}/assets/images/jobscheduler_template_jobchain.png)

以下のようなシナリオを想定します。
serverAでjobAが稼働中は利用可能メモリ量が50MBより小さい場合にトリガーを発動するようにしたい。

![architecture]({{ site.production_url }}/assets/images/sample_jobchain.png)

この場合は以下の手順でjobAが稼働する前後でトリガー変更テンプレートジョブが実行するようにJob Chainの設定をして下さい。

### ジョブテンプレートのコピー

JobSchedulerのhyclops_jmディレクトリ内にある以下のジョブをserverAのディレクトリにコピーして下さい

* HyClops_JM_Trigger_switch.job.xml
* HyClops_JM_Trigger_ret.job.xml
* target_zabbix_host.xml

### Job Chainの作成

以下の実行順になるようJob Chainを設定して下さい

<pre>
(1)HyClops_JM_Trigger_switch => (2)jobA => (3)HyClops_JM_Trigger_ret
</pre>

### 対象のZabbixホスト名の設定

target_zabbix_host.xml内にトリガーしきい値を変更する対象となるZabbixのホスト名を設定して下さい

<pre>
&lt;params>
  &lt;!-- valueに対象のZabbixホスト名を設定して下さい -->
  &lt;param name="zabbix_host" value="localhost"/>
&lt;/params>
</pre>

### 変更前後のトリガー設定

HyClops_JM_Trigger_switch.job.xmlのパラメータを設定して下さい

<pre>
&lt;params>
  &lt;include live_file="target_zabbix_host.xml" node=""/>
  &lt;!-- 変更対象となるトリガー名を指定。トリガー名はZabbix Web UIから確認可能な名前を指定。 -->
  &lt;param name="trigger_name" value="Lack of available memory on server {HOST.NAME}"/>
  &lt;!-- 変更後に有効となるトリガー条件式を指定。 -->
  &lt;param name="trigger_cond" value="{localhost:vm.memory.size[available].last(0)}<50M"/>
&lt;/params>
</pre>

これらの設定によって、jobAが稼働する前処理でトリガーしきい値の変更ジョブが稼働し、jobAが稼働し終わった後でトリガーを元に戻す後処理が稼働します。

# 問い合わせ先 {#contact}

フィードバックや不明点等以下までお問い合わせ下さい。

[TIS株式会社](http://www.tis.co.jp)  
コーポレート本部　戦略技術センター  
HyClops JobMonitoring 担当宛  
<hyclops@ml.tis.co.jp>


# ライセンス {#license}

HyClops JobMonitoringはApache License, Version 2.0のもとにリリースされています。  
ライセンスの全文は [こちら](http://www.apache.org/licenses/LICENSE-2.0) からご覧頂くことが可能です。

