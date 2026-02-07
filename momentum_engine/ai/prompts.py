"""
Prompt Templates for AI Operations
"""

PROMPTS = {
    "task_selection": """You are an IELTS tutor selecting the next practice task.

User's recent performance:
{recent_tasks}

Weak areas: {weak_areas}

Available task IDs: {available_tasks}

Select the BEST task ID for this user based on their weaknesses.
Respond with ONLY the task ID number, nothing else.""",

    "weekly_report": """Generate a personalized weekly progress report for an IELTS student.

Week {week_number} Summary:
- Tasks completed: {tasks_completed}
- Practice time: {practice_minutes} minutes
- Learning Velocity Score: {lvs}
- Completion Rate: {macr}%

Module Performance:
{module_performance}

Provide:
1. Key achievements (2-3 sentences, be specific and encouraging)
2. Areas needing focus (identify 1-2 specific modules)
3. Actionable recommendations for next week (3 bullet points)

Keep it motivating, specific, and under 200 words.""",

    "intervention_diagnosis": """Analyze why this IELTS student is struggling and recommend intervention.

Recent Performance:
{recent_tasks}

Current Accuracy: {accuracy}%
Module: {module}
Consecutive Failures: {failures}

Diagnose the specific issue and recommend ONE intervention from:
- strategy_video: For technique/approach issues
- targeted_practice: For skill gaps
- simplified_exercise: For confidence building

Respond in JSON format:
{{"diagnosis": "brief explanation", "intervention_type": "strategy_video|targeted_practice|simplified_exercise", "specific_recommendation": "detailed suggestion"}}""",

    "personalized_feedback": """Provide brief feedback on this IELTS {module} task.

User's Response:
{user_response}

Task Type: {task_type}
Expected Focus: {expected_focus}

Provide:
1. What they did well (1 sentence)
2. One specific area to improve (1 sentence)
3. Quick tip (1 sentence)

Keep total response under 100 words. Be encouraging but specific.""",
}
