from .models import AudioQualityMetric, CoordinationDecision

class PhoneCoordinationAlgorithm:
    def __init__(self):
        self.quality_weights = {
            'volume_level': 0.3,
            'background_noise': 0.25,
            'clarity_score': 0.25,
            'proximity_score': 0.2
        }
    
    def calculate_overall_score(self, quality_metric):
        """Calculate overall audio quality score for a participant"""
        score = 0
        
        if quality_metric.volume_level is not None:
            score += self.quality_weights['volume_level'] * quality_metric.volume_level
        
        if quality_metric.background_noise is not None:
            # Lower noise is better, so invert the score
            score += self.quality_weights['background_noise'] * (1 - quality_metric.background_noise)
        
        if quality_metric.clarity_score is not None:
            score += self.quality_weights['clarity_score'] * quality_metric.clarity_score
        
        if quality_metric.proximity_score is not None:
            score += self.quality_weights['proximity_score'] * quality_metric.proximity_score
        
        quality_metric.overall_score = score
        quality_metric.save()
        
        return score
    
    def select_primary_recorder(self, meeting):
        """Select the best phone to be the primary recorder"""
        participants = meeting.participants.filter(is_recording=True)
        
        if not participants:
            return None
        
        best_participant = None
        best_score = -1
        
        for participant in participants:
            latest_metric = participant.quality_metrics.latest('created_at')
            if latest_metric:
                score = self.calculate_overall_score(latest_metric)
                if score > best_score:
                    best_score = score
                    best_participant = participant
        
        return best_participant
    
    def create_coordination_decision(self, meeting):
        """Create a coordination decision for the meeting"""
        primary_recorder = self.select_primary_recorder(meeting)
        
        if not primary_recorder:
            return None
        
        # Get backup recorders (other active participants)
        backup_participants = meeting.participants.filter(
            is_recording=True
        ).exclude(id=primary_recorder.id)
        
        decision = CoordinationDecision.objects.create(
            meeting=meeting,
            primary_recorder=primary_recorder,
            algorithm_version='1.0',
            decision_factors={
                'primary_score': primary_recorder.quality_metrics.latest('created_at').overall_score if primary_recorder.quality_metrics.exists() else 0,
                'backup_count': backup_participants.count()
            }
        )
        
        decision.backup_recorders.set(backup_participants)
        
        return decision