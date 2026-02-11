# 项目环境搭建指南

当你首次克隆或拉取项目代码后，请按照以下步骤搭建开发环境：

## 1. 创建并激活虚拟环境（必须）
Python虚拟环境可以隔离项目依赖，避免与全局环境或其他项目冲突。

### Windows系统
- PowerShell：
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- 命令提示符（CMD）：
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate.bat
  ```

### macOS/Linux系统
```bash
python3 -m venv .venv
source .venv/bin/activate
```

激活成功后，命令行提示符前会出现`(.venv)`标识。

## 2. 安装项目依赖
激活虚拟环境后，安装项目所需依赖：
```bash
pip install -r requirements.txt
```

## 3. 验证安装
运行以下命令验证环境是否正常：
```bash
python src/main.py --help
```

如果出现帮助信息，说明环境搭建成功。

## 4. 日常开发流程
每次打开终端开始开发时：
1. 进入项目目录
2. 激活虚拟环境：` .venv\Scripts\Activate.ps1`（Windows PowerShell）
3. 运行项目代码
4. 开发完成后，可通过`deactivate`命令退出虚拟环境

## 常见问题
### Q: 为什么必须使用虚拟环境？
A: 虚拟环境可以隔离项目依赖，避免不同项目之间的版本冲突，保持全局Python环境干净。这类似于前端项目中的`node_modules`目录隔离。

### Q: 如何确认我在虚拟环境中？
A: 查看命令行提示符前是否有`(.venv)`标识，或运行`where python`（Windows）/`which python`（macOS/Linux），路径应指向`.venv`目录下的Python解释器。

### Q: 激活虚拟环境时出现权限错误？
A: 在Windows PowerShell中运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```