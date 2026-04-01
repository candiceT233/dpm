# Extract SPM values for producer-consumer pairs


# idfea+single:
# for the first 3 values we want to select
# # stage_in-run_idfeature+run_idfeature and run_idfeature+run_tracksingle
# # # stage_in-run_idfeature+run_idfeature 
# # # (producerStorageType == beegfs-ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for SSD 4n (first value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for SSD 8n (second value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for SSD 16n (third value)
# # # (producerStorageType == beegfs-tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for BeeGFS 16n (ninth value)
# # # run_idfeature+run_tracksingle 
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for SSD 4n (first value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for SSD 8n (second value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for BeeGFS 16n (ninth value)

# single+tracks:
# for the first 3 values we want to select
# # stage_in-run_tracksingle+run_tracksingle and run_tracksingle+run_gettracks
# # # stage_in-run_tracksingle+run_tracksingle
# # # (producerStorageType == ssd-ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for SSD 4n (first value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for SSD 8n (second value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for SSD 16n (third value)
# # # (producerStorageType == tmpfs-tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for BeeGFS 16n (ninth value)
# # # run_tracksingle+run_gettracks
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for SSD 4n (first value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for SSD 8n (second value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for BeeGFS 16n (ninth value)

# tracks+stats:
# for the first 3 values we want to select
# # stage_in-run_gettracks+run_gettracks and run_gettracks+run_trackstats
# # # stage_in-run_gettracks+run_gettracks
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for SSD 4n (first value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for SSD 8n (second value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for BeeGFS 16n (ninth value)
# # # run_gettracks+run_trackstats
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for SSD 4n (first value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for SSD 8n (second value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 30 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 15 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 8 for BeeGFS 16n (ninth value)

# stats+idfymcs
# for the first 3 values we want to select
# # stage_in-run_trackstats+run_trackstats and run_trackstats+run_identifymcs
# # # stage_in-run_trackstats+run_trackstats
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for SSD 4n (first value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for SSD 8n (second value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 30 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 15 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 8 for BeeGFS 16n (ninth value)
# # # run_trackstats+run_identifymcs
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for SSD 4n (first value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for SSD 8n (second value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 1 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 1 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 8 and consumerTasksPerNode 1 for BeeGFS 16n (ninth value)

# idfymcs+matchpf
# for the first 3 values we want to select
# # stage_in-run_identifymcs+run_identifymcs and run_identifymcs+run_matchpf
# # # stage_in-run_identifymcs+run_identifymcs
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 60 and consumerTasksPerNode 1 for SSD 4n (first value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for SSD 8n (second value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 1 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 1 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for BeeGFS 16n (ninth value)
# # # run_identifymcs+run_matchpf
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for SSD 4n (first value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for SSD 8n (second value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for BeeGFS 16n (ninth value)

# matchpf+robustmcs
# for the first 3 values we want to select
# # stage_in-run_matchpf+run_matchpf and run_matchpf+run_robustmcs
# # # stage_in-run_matchpf+run_matchpf
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 60 and consumerTasksPerNode 1 for SSD 4n (first value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for SSD 8n (second value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 1 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 60 and consumerTasksPerNode 1 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 30 and consumerTasksPerNode 1 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 15 and consumerTasksPerNode 1 for BeeGFS 16n (ninth value)
# # # run_matchpf+run_robustmcs
# # # (producerStorageType == ssd, consumerStorageType == ssd)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for SSD 4n (first value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for SSD 8n (second value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for SSD 16n (third value)
# # # (producerStorageType == tmpfs, consumerStorageType == tmpfs)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for TMPFS 4n (fourth value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for TMPFS 8n (fifth value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for TMPFS 16n (sixth value)
# # # (producerStorageType == beegfs, consumerStorageType == beegfs)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for BeeGFS 4n (seventh value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for BeeGFS 8n (eighth value)
# # # producerTasksPerNode 1 and consumerTasksPerNode 1 for BeeGFS 16n (ninth value)




