"""API views for meeting agenda management"""
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Meeting, AgendaItem


@login_required
def agenda_api(request, meeting_id):
    """Handle agenda API - GET for list, POST for create"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)

    if request.method == 'GET':
        # Get all agenda items for a meeting
        agenda_items = meeting.agenda_items.all().order_by('order', 'created_at')

        return JsonResponse({
            'success': True,
            'agenda_items': [
                {
                    'id': item.id,
                    'title': item.title,
                    'assigned_participant': item.assigned_participant,
                    'participant_name': item.participant_name,
                    'order': item.order,
                    'is_current': meeting.current_agenda_item_id == item.id
                }
                for item in agenda_items
            ]
        })

    elif request.method == 'POST':
        # Create a new agenda item
        title = request.POST.get('title', '').strip()
        assigned_participant = request.POST.get('assigned_participant', '').strip()

        if not title:
            return JsonResponse({'success': False, 'error': 'Title is required'})

        # Get the next order number
        last_item = meeting.agenda_items.order_by('order').last()
        next_order = (last_item.order + 1) if last_item else 0

        agenda_item = AgendaItem.objects.create(
            meeting=meeting,
            title=title,
            assigned_participant=assigned_participant or '',
            order=next_order
        )

        return JsonResponse({
            'success': True,
            'agenda_item': {
                'id': agenda_item.id,
                'title': agenda_item.title,
                'assigned_participant': agenda_item.assigned_participant,
                'participant_name': agenda_item.participant_name,
                'order': agenda_item.order
            }
        })

    else:
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
@require_http_methods(["DELETE"])
def agenda_delete_api(request, meeting_id, item_id):
    """Delete an agenda item"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)
    agenda_item = get_object_or_404(AgendaItem, id=item_id, meeting=meeting)

    agenda_item.delete()

    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def agenda_reorder_api(request, meeting_id):
    """Reorder agenda items"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)

    try:
        data = json.loads(request.body)
        order_data = data.get('order', [])

        # Update order for each item
        for item_data in order_data:
            item_id = item_data.get('id')
            new_order = item_data.get('order')

            if item_id and new_order is not None:
                AgendaItem.objects.filter(
                    id=item_id,
                    meeting=meeting
                ).update(order=new_order)

        return JsonResponse({'success': True})

    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse({'success': False, 'error': 'Invalid data format'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def set_current_agenda_api(request, meeting_id):
    """Set current agenda item for meeting"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, host=request.user)

    try:
        data = json.loads(request.body)
        agenda_item_id = data.get('agenda_item_id')

        if agenda_item_id:
            # Validate that agenda item belongs to this meeting
            agenda_item = get_object_or_404(AgendaItem, id=agenda_item_id, meeting=meeting)
            meeting.current_agenda_item = agenda_item
        else:
            # Clear current agenda item
            meeting.current_agenda_item = None

        meeting.save()

        return JsonResponse({
            'success': True,
            'current_agenda': {
                'id': meeting.current_agenda_item.id if meeting.current_agenda_item else None,
                'title': meeting.current_agenda_item.title if meeting.current_agenda_item else None
            }
        })

    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse({'success': False, 'error': 'Invalid data format'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def current_agenda_api(request, meeting_id):
    """Get current agenda item for meeting"""
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id)

    # Allow both host and participants to view current agenda
    return JsonResponse({
        'success': True,
        'current_agenda': {
            'id': meeting.current_agenda_item.id if meeting.current_agenda_item else None,
            'title': meeting.current_agenda_item.title if meeting.current_agenda_item else None,
            'participant_name': meeting.current_agenda_item.participant_name if meeting.current_agenda_item else None
        } if meeting.current_agenda_item else None
    })