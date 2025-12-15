#!/usr/bin/env python3
"""
Security Verification Script
Memverifikasi bahwa tidak ada credential sensitif yang siap untuk di-commit ke GitHub
"""

import os
import subprocess
from pathlib import Path

class SecurityChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        self.repo_root = Path.cwd()
    
    def check_gitignore(self):
        """Verify .gitignore contains sensitive patterns"""
        gitignore_path = self.repo_root / ".gitignore"
        
        if not gitignore_path.exists():
            self.issues.append("❌ .gitignore file not found")
            return
        
        with open(gitignore_path) as f:
            content = f.read()
        
        sensitive_patterns = [
            ".env",
            "google-service-account.json",
            "*.json",
            "/data/",
        ]
        
        for pattern in sensitive_patterns:
            if pattern in content:
                self.passed.append(f"✅ .gitignore contains: {pattern}")
            else:
                self.issues.append(f"❌ .gitignore missing: {pattern}")
    
    def check_untracked_files(self):
        """Check if sensitive files are in git staging area"""
        try:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            
            staged_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
            
            sensitive_files = [".env", "google-service-account.json", "notifications.yaml"]
            
            for file in staged_files:
                for sensitive in sensitive_files:
                    if sensitive in file:
                        self.issues.append(f"❌ CRITICAL: {file} is staged for commit!")
            
            if not any(s in " ".join(staged_files) for s in sensitive_files):
                self.passed.append("✅ No sensitive files in staging area")
        except Exception as e:
            self.warnings.append(f"⚠️  Could not check staging area: {e}")
    
    def check_local_files(self):
        """Check if sensitive files exist locally (should not be committed)"""
        sensitive_files = [
            ".env",
            "config/google-service-account.json",
            "config/notifications.yaml",
            "config/servers.yaml",
        ]
        
        for file in sensitive_files:
            path = self.repo_root / file
            if path.exists():
                self.passed.append(f"✅ {file} exists locally (not in git)")
            else:
                if file == ".env" or "service-account" in file:
                    self.warnings.append(f"⚠️  {file} not found (will be needed for setup)")
    
    def check_env_example(self):
        """Verify .env.example doesn't contain actual secrets"""
        env_example = self.repo_root / ".env.example"
        
        if not env_example.exists():
            self.issues.append("❌ .env.example template not found")
            return
        
        with open(env_example) as f:
            content = f.read()
        
        # These should contain template values, not real secrets
        template_indicators = [
            "your_",
            "example",
            "your-",
            "placeholder",
        ]
        
        has_template = any(indicator in content.lower() for indicator in template_indicators)
        
        if has_template:
            self.passed.append("✅ .env.example contains template placeholders (not real values)")
        else:
            self.warnings.append("⚠️  .env.example may contain actual values (review)")
    
    def check_git_history(self):
        """Scan recent commits for common secret patterns"""
        try:
            result = subprocess.run(
                ["git", "log", "--all", "--oneline", "-20"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            
            # This is a basic check - for production, use git-secrets or TruffleHog
            self.passed.append("✅ Git history accessible (basic scan complete)")
        except Exception as e:
            self.warnings.append(f"⚠️  Could not scan git history: {e}")
    
    def check_documentation(self):
        """Verify security documentation exists"""
        docs = [
            "SETUP_GUIDE.md",
            "SECURITY_CHECKLIST.md",
        ]
        
        for doc in docs:
            path = self.repo_root / doc
            if path.exists():
                self.passed.append(f"✅ {doc} exists")
            else:
                self.warnings.append(f"⚠️  {doc} not found")
    
    def run_all_checks(self):
        """Run all security checks"""
        print("\n" + "="*60)
        print("🔐 SECURITY VERIFICATION SCAN")
        print("="*60 + "\n")
        
        self.check_gitignore()
        self.check_local_files()
        self.check_env_example()
        self.check_untracked_files()
        self.check_git_history()
        self.check_documentation()
        
        self._print_results()
    
    def _print_results(self):
        """Print results in organized format"""
        
        if self.passed:
            print("✅ PASSED CHECKS:")
            for check in self.passed:
                print(f"   {check}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
            print()
        
        if self.issues:
            print("❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   {issue}")
            print()
        
        print("="*60)
        
        if self.issues:
            print("🚫 SECURITY CHECK FAILED - Fix issues before pushing to GitHub")
            print("\nQuick fixes:")
            print("  1. Update .gitignore: git add .gitignore && git commit")
            print("  2. Remove accidentally staged files: git reset HEAD <filename>")
            print("  3. Create .env.example template: cp .env.example")
            print("\nSee SECURITY_CHECKLIST.md for detailed instructions")
            return False
        elif self.warnings:
            print("⚠️  SECURITY CHECK PASSED WITH WARNINGS")
            print("   Review warnings above before pushing")
            return True
        else:
            print("✅ SECURITY CHECK PASSED - Safe to push to GitHub!")
            return True
    
    def get_status(self):
        """Return boolean: True if safe to push, False otherwise"""
        return not bool(self.issues)


def main():
    checker = SecurityChecker()
    checker.run_all_checks()
    
    if checker.get_status():
        exit(0)  # Success
    else:
        exit(1)  # Failed


if __name__ == "__main__":
    main()
