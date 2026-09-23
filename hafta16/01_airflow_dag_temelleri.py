from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta

def bwa_alignment():
    print("[TASK] BWA-MEM ile hizalama yapılıyor...")
    print("[TASK] Sonuç: %99.5 mapping rate (Hafta 2'deki gerçek sonucun)")
    return "alignment_tamamlandi"

def gatk_variant_calling():
    print("[TASK] GATK4 ile germline varyant çağrısı yapılıyor...")
    print("[TASK] Sonuç: 54 varyant tespit edildi (Hafta 3'teki gerçek sonucun)")
    return "variant_calling_tamamlandi"

def somatic_calling():
    print("[TASK] Somatic varyant analizi (TP53 R175H aranıyor)...")
    print("[TASK] Sonuç: TP53 R175H, AF=0.977 tespit edildi")
    return "somatic_calling_tamamlandi"

def rapor_olustur():
    print("[TASK] R/vcfR ile klinik rapor oluşturuluyor...")
    print("[TASK] Rapor hazır: klinik_rapor.pdf")
    return "rapor_tamamlandi"

varsayilan_ayarlar = {
    "owner": "gizem",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="ngs_pipeline_orkestrasyon",
    default_args=varsayilan_ayarlar,
    description="Hafta 1-9 NGS pipeline'ının Airflow ile orkestrasyonu",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ngs", "genomik", "hafta16"],
) as dag:

    task_alignment = PythonOperator(
        task_id="bwa_alignment",
        python_callable=bwa_alignment,
    )

    task_variant_calling = PythonOperator(
        task_id="gatk_variant_calling",
        python_callable=gatk_variant_calling,
    )

    task_somatic = PythonOperator(
        task_id="somatic_calling",
        python_callable=somatic_calling,
    )

    task_rapor = PythonOperator(
        task_id="rapor_olustur",
        python_callable=rapor_olustur,
    )

    task_alignment >> task_variant_calling >> task_somatic >> task_rapor