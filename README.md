# 芦湾教研 · 泳池水感课观察维度

从匿名教学观察中归纳课堂感受的两个维度。在教研核校通过后，用载荷证据修订下一轮观察表，并保留旧轮次的版本。

芦湾游泳中心的五人教研组轮流观察晨课、午间课和晚课。以前用纸表收集，再在共享表格里汇总。小班的人数和分档经常一起外发；有的观察员把表述为负面的项目直接加总；修订问卷时覆盖了旧表结构。工作台将回收、核校、修订连成一个流程。教学观察员录入匿名券和评分，教研人员确认分析，再把新版开放给下一轮课堂观察。

项目用模拟数据展示课堂观察与问卷版次。没有处理泳池水质、化学品、授课安全或实训操作。

| 账号 | 角色 | 工作 |
|---|---|---|
| shu | technician / 科目观察 | 核对回收进度、录入匿名问卷、冻结并申请拟合 |
| fang | supervisor / 教研核校 | 核校因子、核对反向项目、签发新版本并开放下一轮 |
| cheng | viewer / 教案查阅 | 只读获得已核校载荷、各版观察表和受门槛控制的回收数字 |

演示密码均为 `Waterline2026!`。

## 教研剧本

1. 11 月 24 日 09:20，观察岗查到 POND-1124 的三个班组回收 10、10、4 份。教案查阅岗看不到晚课组的具体数字。
2. 09:25，尝试拟合时收到 COACH-C 未满 8 份的提示，系统仍允许补采。
3. 10:10，使用四张一次性观察券补录；未同意匿名汇总、重复券和缺题会被拒绝。
4. 10:35，晚课组达到 8 份，合计 28 份。观察岗冻结本轮后才送入合并因子拟合。
5. 11:00，教研核校岗查看两条反向项目 CW-03、CW-06 和两个正交因子载荷。
6. 11:20，核校通过后保留固定的 CW-01 和两个维度的代表项。选定四项发为 LW-02。
7. 11:25，POND-1124 被封存，旧版 LW-01 归档。POND-1201 持有新版数量和班组名册，开始新一轮观察。

## 模型与保护

各教练组至少 8 份、整个轮次至少 24 份，全部达到门槛才允许合并。观测记录不采集参与者姓名、联系方式或自由文本，不提供逐人明细。观察券按轮次哈希去重。所有长期保存的报告只有整轮载荷和统计，不输出各教练组的独立模型。查阅角色在低于门槛时仅能看到待补采标记。

反向题转为 `6 - 原始分`，然后逐项标准化。Python worker 运行 sklearn 的两因子 FactorAnalysis，旋转为 varimax。模型保存每项载荷、共同度和残差、完整样本数、迭代数、输入摘要和种子 1084。常量题或未收敛时退回收集，原轮次重新开放。新表至少保留四题，必须包含固定的开场题和对每个因子主要载荷绝对值至少 0.45 的题。版本切换、新轮次及旧轮次封存在同一事务提交。

## 运行

```sh
cp .env.example .env
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
docker compose down -v --remove-orphans
```

工作台位于 `http://127.0.0.1:18308/`，接口文档位于 `http://127.0.0.1:19308/docs`。数据库在本机映射 17808，Redis 不映射宿主端口。

| 服务 | 技术和职责 |
|---|---|
| frontend | 原生 HTML/CSS/JS 与 Nginx /api 代理 |
| backend | Python 3.12、FastAPI、JWT、SQLAlchemy、审计 |
| worker | Redis 通知、数据库持久队列与 Python FactorAnalysis |
| db | PostgreSQL 16 事务、版本、题目、观察和组关联 |
| redis | Redis 7 唤醒队列与 AOF |

`.env.example` 包含三个映射端口、DB_NAME/DB_USER/DB_PASSWORD、JWT_SECRET 和 SEED_DEMO。本地开发终端可另行指定 DATABASE_URL、REDIS_URL，按 `backend/requirements.txt` 装依赖，再分别运行 `uvicorn pool.app:app --reload` 与 `python -m pool.worker`。数据模型和服务在 `backend/pool`，演示脚本在 `backend/scripts`，页面、状态和组件在 `frontend/src`。

轮次、报告、表单和角色值在 `backend/pool/constants.py` 声明，由 `cohorts.py`、`survey_routes.py`、`report_control.py`、`report_routes.py`、`form_control.py` 使用。前端对应 `frontend/src/types.js`，由 `pages/waves.js`、`pages/loadings.js`、`pages/forms.js` 和 `components/desk.js` 消费。本应用随工作区交付，当前没有单独开源许可证。
