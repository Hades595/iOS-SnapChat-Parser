SELECT 
    snap_id_table.snap_id,
    snap_description_table.caption,
    snap_time_tag_table.time_tag
FROM 
    snap_id_table
JOIN snap_description_table ON snap_description_table.ROWID = snap_id_table.ROWID 
JOIN snap_time_tag_table ON snap_time_tag_table.snap_id = snap_id_table.snap_id
ORDER BY time_tag ASC