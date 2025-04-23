from datetime import datetime
from pathlib import Path
now = datetime.now()
str = now.strftime("%Y%m%d")
print(str)
today = datetime.now().strftime("%Y%m%d")
res = Path("/www/wwwlogs").glob(f"*.log")
for file in res:
    print(file)