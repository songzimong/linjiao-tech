# Python 自动化办公：30 分钟搞定重复工作

> 作者：麟角科技 · 寸铁杀人，滴水穿石

---

## 你每天都在浪费时间做的事

- 把 Excel 里的数据整理成报告
- 给几百个文件夹里的文件重命名
- 每天从邮件里下载附件并汇总
- 把 PDF 里的表格提取出来

这些工作，程序员花 30 分钟写个脚本，你可以**永远不再做**。

---

## 什么是 Python 自动化办公？

简单来说：用 Python 写小程序，让电脑自动完成那些**重复、无聊、耗时间**的工作。

不需要你是程序员。下面的例子，你只需要复制粘贴，改几个文件名就能用。

---

## 实战一：批量重命名文件

**场景：** 你下载了 100 张图片，文件名全是 `IMG_001.jpg`、`IMG_002.jpg`，你想改成 `项目A_001.jpg`、`项目A_002.jpg`。

```python
import os

folder = r"C:\Users\你的用户名\Downloads\照片"

for i, filename in enumerate(os.listdir(folder)):
    if filename.endswith(".jpg"):
        old_path = os.path.join(folder, filename)
        new_name = f"项目A_{i+1:03d}.jpg"
        new_path = os.path.join(folder, new_name)
        os.rename(old_path, new_path)
        print(f"已重命名: {filename} → {new_name}")

print("✅ 全部完成！")
```

**效果：** 100 个文件，3 秒钟搞定。

---

## 实战二：Excel 数据汇总

**场景：** 你有 10 个 Excel 文件，每个文件有销售数据，你想把它们合并成一个总表。

```python
import pandas as pd
import glob
import os

folder = r"C:\Users\你的用户名\销售数据"
all_files = glob.glob(os.path.join(folder, "*.xlsx"))

combined = pd.DataFrame()
for file in all_files:
    df = pd.read_excel(file)
    combined = pd.concat([combined, df], ignore_index=True)

combined.to_excel("总报表.xlsx", index=False)
print(f"✅ 已合并 {len(all_files)} 个文件")
```

**效果：** 原本需要 2 小时的手工操作，现在 10 秒完成。

---

## 实战三：自动发送邮件

**场景：** 每个月要给 50 个客户发送账单邮件，内容差不多，只是名字和金额不同。

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd

# 读取客户数据
data = pd.read_excel("客户列表.xlsx")

smtp_server = "smtp.qq.com"
smtp_port = 587
sender_email = "your@qq.com"
sender_password = "你的授权码"

for _, row in data.iterrows():
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = row["邮箱"]
    msg["Subject"] = f"{row['姓名']}，您的月度账单"
    
    body = f"""
    尊敬的 {row['姓名']}：

    您本月的账单金额为：¥{row['金额']}
    请于 5 个工作日内完成支付。

    如有疑问，请联系我们。

    此致
    麟角科技
    """
    
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()
    
    print(f"✅ 已发送给: {row['姓名']}")

print("🎉 全部邮件发送完成！")
```

**效果：** 50 封邮件，全自动发送，不用你动手。

---

## 为什么你应该学 Python？

1. **省时** — 一小时的工作，脚本 10 秒搞定
2. **省钱** — 不需要雇人做重复性工作
3. **省力** — 不用天天加班整理数据
4. **增值** — 学会后可以做更多事

---

## 从零开始

如果你从来没有写过代码，建议从这里入手：

1. 安装 Python：`python.org` 下载安装
2. 安装编辑器：VS Code（免费）
3. 安装需要的库：`pip install pandas openpyxl`
4. 从上面的例子开始改

**不需要报班，不需要买课。** 网上免费资源足够入门。

---

## 关于麟角科技

我们是麟角科技，一家专注于自动化办公和技术服务的小团队。

如果你不想自己写代码，我们可以帮你：
- 定制自动化脚本
- 搭建数据处理流程
- 开发企业内部工具

**联系方式：** 通过电鸭社区或知乎私信联系我们。

---

> 寸铁杀人，滴水穿石。
> 用最简单的工具，解决最实际的问题。
