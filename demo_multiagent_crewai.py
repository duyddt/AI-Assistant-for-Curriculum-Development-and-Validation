"""
Demo: He thong 4-agent viet bao cao tu dong ve "Multi-agent trong Agentic AI"
Framework: CrewAI
Cach chay: python demo_multiagent_crewai.py
Yeu cau: da cai `pip install crewai` va da set bien moi truong GROQ_API_KEY
(dang ky mien phi, khong can the tai https://console.groq.com)
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# Nap bien moi truong tu file .env (neu co) nam cung thu muc voi file nay
load_dotenv()

# ---------------------------------------------------------------
# 0. Kiem tra API key truoc khi chay (bao loi ro rang thay vi lang)
#    Dung Groq (mien phi, khong can the) thay vi OpenAI (tra phi)
# ---------------------------------------------------------------
_key = os.getenv("GROQ_API_KEY", "")
if not _key or "xxxx" in _key.strip().lower():
    raise SystemExit(
        "GROQ_API_KEY chua duoc dat hoac van la gia tri mau.\n"
        "  1) Dang ky mien phi (khong can the) tai https://console.groq.com\n"
        "  2) Vao 'API Keys' -> tao key moi\n"
        "  3) Mo file .env cung thu muc, dan key vao dong GROQ_API_KEY=\n"
        "  Hoac set truc tiep trong terminal truoc khi chay:\n"
        "     Windows (PowerShell):  $env:GROQ_API_KEY='gsk_...'\n"
        "     macOS/Linux:           export GROQ_API_KEY='gsk_...'\n"
    )


llm = LLM(
    model="openai/openai/gpt-oss-20b", 
    base_url="https://api.groq.com/openai/v1",
    api_key=_key,
)

# ---------------------------------------------------------------
# 1. Dinh nghia 4 Agent - dung vai tro nhu trong slide demo
# ---------------------------------------------------------------
researcher = Agent(
    role="Researcher",
    goal="Thu thap va tong hop cac y chinh, dinh nghia, vi du thuc te "
         "ve kien truc Multi-agent trong Agentic AI",
    backstory=(
        "Ban la mot nha nghien cuu AI, chuyen tim kiem va chat loc thong tin "
        "chinh xac, ngan gon tu kien thuc chuyen mon."
    ),
    llm=llm,
    verbose=True,
)

analyst = Agent(
    role="Analyst",
    goal="Phan tich thong tin do Researcher cung cap, rut ra 4-5 y chinh "
         "co logic ro rang, loai bo thong tin trung lap",
    backstory=(
        "Ban la chuyen gia phan tich noi dung, giỏi sap xep y tuong "
        "theo cau truc logic de nguoi doc de theo doi."
    ),
    llm=llm,
    verbose=True,
)

writer = Agent(
    role="Writer",
    goal="Viet mot bao cao ngan (300-450 tu) bang tieng Viet ve Multi-agent "
         "trong Agentic AI, dua tren cac y chinh cua Analyst",
    backstory=(
        "Ban la nguoi viet ky thuat, giỏi trinh bay noi dung ro rang, "
        "co mo dau - than bai - ket luan."
    ),
    llm=llm,
    verbose=True,
)

reviewer = Agent(
    role="Reviewer",
    goal="Kiem tra ban bao cao cua Writer: logic, day du y, khong loi "
         "chinh ta, gop y chinh sua neu can",
    backstory=(
        "Ban la bien tap vien khó tinh, luon doc ky truoc khi duyet "
        "mot van ban ky thuat."
    ),
    llm=llm,
    verbose=True,
)

# ---------------------------------------------------------------
# 2. Dinh nghia Task cho tung Agent (dung thu tu = pipeline)
# ---------------------------------------------------------------
task_research = Task(
    description=(
        "Liet ke cac y chinh ve: (1) dinh nghia Multi-agent AI, "
        "(2) vi sao can nhieu agent thay vi 1 agent, "
        "(3) cac thanh phan trong kien truc multi-agent "
        "(orchestrator, worker agent, shared memory, tools)."
    ),
    expected_output="Danh sach gach dau dong cac y chinh, kem giai thich ngan.",
    agent=researcher,
)

task_analyze = Task(
    description=(
        "Tu ket qua cua Researcher, rut gon con 4-5 y quan trong nhat, "
        "sap xep theo thu tu hop ly de viet bao cao."
    ),
    expected_output="4-5 y chinh da duoc sap xep logic.",
    agent=analyst,
    context=[task_research],
)

task_write = Task(
    description=(
        "Viet bao cao hoan chinh (300-450 tu) bang tieng Viet, co tieu de, "
        "mo dau, 2-3 doan than bai theo cac y cua Analyst, va ket luan."
    ),
    expected_output="Bai bao cao hoan chinh dang van ban.",
    agent=writer,
    context=[task_analyze],
)

task_review = Task(
    description=(
        "Doc lai bao cao cua Writer, kiem tra tinh day du, logic va chinh ta. "
        "Neu on, xac nhan 'Da duyet'. Neu can sua, ghi ro cho tiet can sua "
        "va tra ve ban da chinh sua."
    ),
    expected_output="Ban bao cao cuoi cung (da duoc duyet/chinh sua).",
    agent=reviewer,
    context=[task_write],
)

# ---------------------------------------------------------------
# 3. Gom thanh Crew - dieu phoi tuan tu (Sequential)
# ---------------------------------------------------------------
crew = Crew(
    agents=[researcher, analyst, writer, reviewer],
    tasks=[task_research, task_analyze, task_write, task_review],
    process=Process.sequential,
    verbose=True,
)

# ---------------------------------------------------------------
# 4. Chay demo
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("BAT DAU DEMO MULTI-AGENT (CrewAI)")
    print("=" * 60)

    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("KET QUA CUOI CUNG (da qua Reviewer)")
    print("=" * 60)
    print(result)
