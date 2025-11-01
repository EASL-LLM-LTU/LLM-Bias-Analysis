When executing the script prompt_level_analysis.py a directory called prompt_analysis_results will be created containing the following:

1. prompt_top_overall.csv - Top 15 bias-triggering prompts
2. prompt_top_by_discipline.csv - Top 8 per discipline
3. keywords_support.csv - Overall keyword patterns
4. keywords_by_discipline.csv - Cross-discipline keyword comparison
5. summary_statistics.csv - Summary metrics in clean CSV format

The script consumes the file finalscores_allstreams.csv containing the columns: output_id,output,prompt_id,prompt,alpha,beta,mode,var,ci_80_lower,ci_80_upper,ci_width,discipline,model
