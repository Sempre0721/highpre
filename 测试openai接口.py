from openai import OpenAI
client = OpenAI(
        api_key="EofwojbrKQpYiFdIGBNW:WxSxTTMZBTooLcoiFWEd", 
        base_url = 'https://spark-api-open.xf-yun.com/v1' # 指向讯飞星火的请求地址
    )
completion = client.chat.completions.create(
    model='4.0Ultra', # 指定请求的版本
    messages=[
        {
            "role": "user",
            "content": '说一个程序员才懂的笑话'
        }
    ]
)
print(completion.choices[0].message)
