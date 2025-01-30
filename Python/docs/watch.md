# **Safer Payments Journal Import Process**

## **1. Overview**
The journal import process in Safer Payments follows a structured pipeline across **Development (Dev) → Quality Assurance (QA) → Deployment Integration Testing (DIT)**. Each environment progresses through different versions of the journal, ensuring stability and validation before promotion.

The process is **automated using Consul Watch & Trigger mechanisms**, ensuring that each environment executes the correct journal version at the right stage.

---

## **2. Step-by-Step Process**

### **A. Journal Export from Dev Model → S3 Staging**
1. The latest journal **Version Vn** is **exported** from the **Dev Model**.
2. The exported journal is **uploaded to S3 Staging**.

### **B. Consul Seeder Job Updates KV Store**
3. The **Consul Seeder** updates the journal versions in the **Consul Key-Value (KV) Store**:
   - `journal_version/dev` → **Vn** (Latest version for Dev execution)
   - `journal_version/qa` → **Vn-1** (Previous version under QA validation)
   - `journal_version/dit` → **Vn-2** (Older version still in DIT, awaiting QA promotion)

### **C. Consul Watch Detects Changes & Triggers Execution**
4. Each environment has a **Consul Watch job** that continuously monitors its assigned journal version:
   - **Dev Execution:** Watches for updates to `journal_version/dev`.
   - **QA Execution:** Watches for updates to `journal_version/qa`.
   - **DIT Execution:** Watches for updates to `journal_version/dit`.
5. When a version change is detected, the corresponding **Download Journal** job is triggered.

### **D. Journal Download & Import Execution**
6. **Download Journal Jobs** pull the assigned version from **S3 Staging**:
   - **Dev Execution:** Downloads **Vn** and starts the import process.
   - **QA Execution:** Downloads **Vn-1** and starts the import process.
   - **DIT Execution:** Downloads **Vn-2** and starts the import process.
7. Each environment executes the **Journal Import process** after downloading.

### **E. Promotion & Iteration**
8. Once **Dev Execution** successfully imports **Vn**, it is promoted to QA:
   - `journal_version/qa` is updated to **Vn**.
   - **QA Execution downloads and imports Vn.**
9. After **QA Execution validates Vn**, it is promoted to DIT:
   - `journal_version/dit` is updated to **Vn-1**.
   - **DIT Execution downloads and imports Vn-1.**
10. The process iterates, ensuring each environment is always **one step behind the latest version until validated**.

---

## **3. Version Mapping Across Environments**

| **Environment**   | **Journal Version in Consul** | **Source (S3 Staging)** |
|------------------|-----------------------------|------------------------|
| **Dev Execution** | **Vn** (Latest exported)    | Pulled from **S3 (Vn)**  |
| **QA Execution**  | **Vn-1** (Under validation) | Pulled from **S3 (Vn-1)** |
| **DIT Execution** | **Vn-2** (Awaiting QA approval) | Pulled from **S3 (Vn-2)** |

---

## **4. Summary of Key Components**
### **A. S3 Staging**
- Stores exported journal versions (**Vn, Vn-1, Vn-2**).
- Each environment pulls only its assigned version from S3.

### **B. Consul Key-Value Store**
- Maintains versioning for each environment (**Dev, QA, DIT**).
- Version updates happen only after successful validation.

### **C. Consul Watch & Triggers**
- **Monitors journal version changes** in Consul.
- **Triggers execution** when a version update occurs.

### **D. Execution Process**
1. **Download Journal** → Fetches the assigned version from S3.
2. **Journal Import Execution** → Runs the import script in each environment.
3. **Promotion** → Moves versions forward only after successful validation.

---

## **5. Benefits of This Process**
✔ **Ensures Stability** → No environment auto-upgrades without validation.  
✔ **Automated Execution** → No manual intervention is needed for imports.  
✔ **Controlled Rollout** → Reduces risks with incremental promotion.  
✔ **Scalable** → Can easily extend to more environments.  
✔ **Consistent Versioning** → Guarantees structured updates across Dev, QA, and DIT.  

This workflow ensures a **safe, automated, and structured approach** to journal imports in Safer Payments. 🚀
