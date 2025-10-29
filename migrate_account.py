"""
One-time script to encrypt existing plaintext passwords in the database.
Run this script once after deploying the new encryption feature.
"""
from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal
from models import EmailAccount
from utils import encrypt_data, decrypt_data
from cryptography.fernet import InvalidToken

def migrate_passwords():
    print("Starting password migration...")
    db = SessionLocal()
    accounts_to_update = 0
    
    try:
        # Get all accounts
        accounts = db.query(EmailAccount).all()
        
        if not accounts:
            print("No accounts found. Exiting.")
            return

        print(f"Found {len(accounts)} accounts to check.")

        for account in accounts:
            print(f"Checking account: {account.email_address}...")
            
            try:
                # 1. Try to decrypt the password
                decrypt_data(account.password)
                # 2. If successful, it's already encrypted.
                print("  -> Password is already encrypted. Skipping.")
                
            except InvalidToken:
                # 3. If decryption fails, it's plaintext. Encrypt it.
                print(f"  -> Plaintext password found. Encrypting now...")
                try:
                    plaintext_password = account.password
                    account.password = encrypt_data(plaintext_password)
                    db.add(account)
                    accounts_to_update += 1
                    print("  -> Successfully encrypted and staged for commit.")
                except Exception as e:
                    print(f"  -> ❌ FAILED to encrypt password for {account.email_address}: {e}")
            
            except Exception as e:
                print(f"  -> ❌ An unexpected error occurred for {account.email_address}: {e}")

        # 4. Commit all changes to the database
        if accounts_to_update > 0:
            db.commit()
            print(f"\n✅ Successfully encrypted {accounts_to_update} passwords.")
        else:
            print("\n✅ All passwords were already encrypted. No changes made.")

    except Exception as e:
        print(f"\n❌ An error occurred during the migration process: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_passwords()
