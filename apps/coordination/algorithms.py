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
        """Select primary recorder - ADMIN/HOST ONLY for now"""
        # ADMIN-ONLY RECORDING: Only consider host/admin participants
        participants = meeting.participants.filter(
            is_recording=True,
            user=meeting.host  # Only the meeting host can be primary recorder
        )

        if not participants:
            return None

        # Since we're only allowing host recording, return the first (and only) host participant
        return participants.first()

        # Future multi-device code (commented out for now):
        # best_participant = None
        # best_score = -1
        #
        # for participant in participants:
        #     latest_metric = participant.quality_metrics.latest('created_at')
        #     if latest_metric:
        #         score = self.calculate_overall_score(latest_metric)
        #         if score > best_score:
        #             best_score = score
        #             best_participant = participant
        #
        # return best_participant
    
    def create_coordination_decision(self, meeting):
        """Create coordination decision - ADMIN-ONLY recording"""
        primary_recorder = self.select_primary_recorder(meeting)

        if not primary_recorder:
            return None

        # ADMIN-ONLY: No backup recorders needed since only host records
        # All other participants are viewers only
        decision = CoordinationDecision.objects.create(
            meeting=meeting,
            primary_recorder=primary_recorder,
            algorithm_version='2.0-admin-only',
            decision_factors={
                'recording_mode': 'admin_only',
                'primary_is_host': True,
                'backup_count': 0  # No backups in admin-only mode
            }
        )

        # No backup recorders in admin-only mode
        # decision.backup_recorders.set([])

        return decision