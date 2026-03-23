import os
import shutil
import sys
from pathlib import Path

def setup_rb_protocol():
    print("🚓 Starting RB-Protocol Drop-in Installer v2.0...")
    
    # 1. Determine Paths
    try:
        bootstrap_dir = Path(__file__).resolve().parent
        project_root = bootstrap_dir.parent
        payload_dir = bootstrap_dir / "payload"
        template_file = bootstrap_dir / "template_rules.yaml"
        
        print(f"🔍 Project Root detected: {project_root}")
    except Exception as e:
        print(f"❌ Error determining paths: {e}")
        sys.exit(1)

    # 2. Find Global Error-DB
    # Primary location provided in docs
    global_error_db = Path(r"C:\Workflow\___111___Antigravity-Projekte\03_ERROR_DB.md")
    
    # Optional search if not found at primary location
    if not global_error_db.exists():
        print(f"⚠️ Global Error-DB not found at {global_error_db}")
        # Could add more search logic here if needed
    else:
        print(f"✅ Found Global Error-DB: {global_error_db}")

    # 3. Create Target Directories
    scripts_target = project_root / "scripts"
    docs_target = project_root / "docs" / "_rb"
    
    scripts_target.mkdir(parents=True, exist_ok=True)
    docs_target.mkdir(parents=True, exist_ok=True)

    # 4. Copy Payload
    try:
        print("📦 Copying framework scripts...")
        shutil.copytree(payload_dir / "scripts", scripts_target, dirs_exist_ok=True)
        
        print("📦 Copying protocol documentation...")
        shutil.copytree(payload_dir / "docs" / "_rb", docs_target, dirs_exist_ok=True)
        
    except Exception as e:
        print(f"❌ Error copying payload: {e}")
        sys.exit(1)

    # 5. Create .rb_protokollrules
    try:
        print("📝 Configuring .rb_protokollrules...")
        if template_file.exists():
            content = template_file.read_text(encoding="utf-8")
            
            # Placeholders
            project_name = project_root.name
            error_db_path = str(global_error_db)
            
            content = content.replace("{{PROJECT_NAME}}", project_name)
            content = content.replace("{{ERROR_DB_PATH}}", error_db_path)
            
            rules_path = project_root / ".rb_protokollrules"
            rules_path.write_text(content, encoding="utf-8")
            print(f"✅ Created {rules_path}")
        else:
            print("⚠️ template_rules.yaml missing, skipping rule generation.")
    except Exception as e:
        print(f"❌ Error creating rules: {e}")

    # 6. Self-Destruct (Optional/Default)
    # The user asked for "Optionally self-destruct", I'll make it default but add a check
    print("\n✅ RB-Protocol successfully installed!")
    
    confirm = input("🗑️ Remove rb_bootstrap folder? (Y/n): ").strip().lower()
    if confirm in ('y', 'yes', ''):
        try:
            # We need to be careful not to delete while running if we are inside
            # But shutil.rmtree on the bootstrap_dir should work if we close the script correctly
            # Or we can do it via a small delay or just tell the user.
            # Actually, shutil.rmtree(bootstrap_dir) might fail if the script is open.
            # Best way is to do it at the very end or ask the user to do it.
            print(f"🚀 Self-destructing {bootstrap_dir}...")
            # On Windows, deleting the directory while a file inside is running can be tricky.
            # We'll try it, if it fails, we tell the user.
            os.system(f'timeout /t 1 > nul && rd /s /q "{bootstrap_dir}"')
            print("👋 Bye!")
        except Exception as e:
            print(f"⚠️ Could not delete bootstrap folder automatically: {e}")
            print(f"💡 Please remove {bootstrap_dir} manually.")
    else:
        print(f"ℹ️ Folder {bootstrap_dir} kept.")

if __name__ == "__main__":
    setup_rb_protocol()
