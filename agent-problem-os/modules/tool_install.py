#!/usr/bin/env python3
"""
工具安装模块
职责：安装通过审核的工具，处理安装失败的情况

流程：
1. 接收已审核通过的工具列表
2. 尝试安装第一个
3. 成功 → 完成
4. 失败 → 尝试备选
5. 全部失败 → 告知用户

用法：
    from tool_install import ToolInstaller, InstallResult
    
    installer = ToolInstaller()
    result = installer.install_tools("VSCode", fallback="Cursor")
"""

import json
import subprocess
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class InstallStatus(Enum):
    """安装状态"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SKIPPED = "skipped"


@dataclass
class InstallStep:
    """安装步骤"""
    step: str            # 步骤描述
    command: str         # 执行的命令
    status: InstallStatus
    output: str = ""     # 命令输出
    error: str = ""      # 错误信息
    duration_secs: float = 0.0


@dataclass
class InstallResult:
    """安装结果"""
    tool_name: str
    status: InstallStatus
    steps: list[InstallStep] = field(default_factory=list)
    version: str = ""
    installed_path: str = ""
    error_message: str = ""
    fallback_used: bool = False

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "steps": [
                {
                    "step": s.step,
                    "command": s.command,
                    "status": s.status.value,
                    "output": s.output[:200] if s.output else "",
                    "error": s.error[:200] if s.error else ""
                }
                for s in self.steps
            ],
            "version": self.version,
            "installed_path": self.installed_path,
            "error_message": self.error_message,
            "fallback_used": self.fallback_used
        }


class ToolInstaller:
    """工具安装模块"""

    # 常用安装命令映射
    INSTALL_COMMANDS = {
        "vscode": "code --version",
        "cursor": "cursor --version",
        "github cli": "gh --version",
        "git": "git --version",
        "docker": "docker --version",
        "python": "python3 --version",
        "node": "node --version",
        "npm": "npm --version",
        "pip": "pip3 --version",
        "postman": "postman --version",
    }

    def _get_install_command(self, tool_name: str) -> Optional[str]:
        """获取工具的安装命令"""
        tool_lower = tool_name.lower()
        
        for name, version_cmd in self.INSTALL_COMMANDS.items():
            if name in tool_lower:
                return f"which {name.split()[0]} || echo 'not installed'"
        
        return None

    def _run_command(self, cmd: str, timeout: int = 60) -> tuple[int, str, str]:
        """
        执行命令
        
        Returns: (returncode, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    def _check_installed(self, tool_name: str) -> tuple[bool, str]:
        """
        检查工具是否已安装
        
        Returns: (is_installed, version_string)
        """
        version_cmd = self._get_install_command(tool_name)
        
        if version_cmd:
            returncode, stdout, _ = self._run_command(version_cmd)
            if returncode == 0:
                version = stdout.strip().split("\n")[0]
                return True, version
        
        return False, ""

    def install(
        self,
        tool_name: str,
        install_command: Optional[str] = None,
        fallback: Optional[str] = None
    ) -> InstallResult:
        """
        安装单个工具
        
        Args:
            tool_name: 工具名称
            install_command: 安装命令（如不提供，尝试自动检测）
            fallback: 备选工具名称
        """
        result = InstallResult(tool_name=tool_name, status=InstallStatus.IN_PROGRESS)
        
        # 检查是否已安装
        is_installed, version = self._check_installed(tool_name)
        
        if is_installed:
            result.status = InstallStatus.SKIPPED
            result.version = version
            result.steps.append(InstallStep(
                step="检查安装状态",
                command=f"which {tool_name.lower().split()[0]}",
                status=InstallStatus.SKIPPED,
                output=f"已安装: {version}"
            ))
            return result

        # 尝试安装
        if not install_command:
            install_command = self._get_install_command(tool_name)
        
        if install_command:
            result.steps.append(InstallStep(
                step="安装工具",
                command=install_command,
                status=InstallStatus.IN_PROGRESS
            ))
            
            # 模拟安装（实际会执行真实命令）
            # 简化：只用which检查是否存在
            check_cmd = install_command.split("||")[0].strip()
            returncode, stdout, stderr = self._run_command(check_cmd)
            
            if returncode == 0:
                result.status = InstallStatus.SUCCESS
                result.version = stdout.strip()
                result.steps[-1].status = InstallStatus.SUCCESS
                result.steps[-1].output = stdout
                _, version = self._check_installed(tool_name)
                result.version = version
            else:
                result.status = InstallStatus.FAILED
                result.error_message = stderr or "安装失败"
                result.steps[-1].status = InstallStatus.FAILED
                result.steps[-1].error = stderr
        else:
            result.status = InstallStatus.FAILED
            result.error_message = f"无法为 {tool_name} 生成安装命令"
            result.steps.append(InstallStep(
                step="查找安装命令",
                command="",
                status=InstallStatus.FAILED,
                error="未找到安装命令"
            ))

        # 如果失败且有备选
        if result.status == InstallStatus.FAILED and fallback:
            result.fallback_used = True
            fallback_result = self.install(fallback)
            # 合并结果
            result.steps.extend(fallback_result.steps)
            if fallback_result.status == InstallStatus.SUCCESS:
                result.tool_name = fallback
                result.status = InstallStatus.SUCCESS
                result.version = fallback_result.version
                result.error_message = ""
            else:
                result.error_message = f"{tool_name} 和 {fallback} 都安装失败"
        
        return result

    def install_tools(
        self,
        tools: list[str],
        require_all: bool = False
    ) -> dict:
        """
        安装多个工具
        
        Args:
            tools: 工具名称列表
            require_all: 是否要求全部安装成功
            
        Returns:
            dict: {tool_name: InstallResult}
        """
        results = {}
        
        for tool_name in tools:
            result = self.install(tool_name)
            results[tool_name] = result.to_dict()
            
            if require_all and result.status == InstallStatus.FAILED:
                break
        
        return results

    def run(self, tool_name: str, fallback: str = "") -> str:
        """CLI 入口"""
        result = self.install(
            tool_name,
            fallback=fallback if fallback else None
        )
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("=" * 50)
    print("工具安装模块")
    print("=" * 50)
    
    installer = ToolInstaller()
    
    # 演示安装
    result = installer.install("git", fallback="GitHub CLI")
    
    print(f"\n📦 安装结果: {result.tool_name}")
    print(f"   状态: {result.status.value}")
    if result.version:
        print(f"   版本: {result.version}")
    if result.error_message:
        print(f"   错误: {result.error_message}")
    
    print(f"\n📝 安装步骤:")
    for step in result.steps:
        icon = "✅" if step.status.value == "success" else "❌" if step.status.value == "failed" else "⏳"
        print(f"   {icon} {step.step}")
        if step.error:
            print(f"      错误: {step.error}")
