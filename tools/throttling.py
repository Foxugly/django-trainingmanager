from rest_framework.throttling import UserRateThrottle


class AIPingThrottle(UserRateThrottle):
    scope = 'ai_ping'


class AIPlanGenerationThrottle(UserRateThrottle):
    scope = 'ai_plan_generation'


class AITrainingGenerationThrottle(UserRateThrottle):
    scope = 'ai_training_generation'
