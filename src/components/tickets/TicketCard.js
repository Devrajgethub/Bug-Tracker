import React from 'react';
import { Draggable } from 'react-beautiful-dnd';

const getPriorityColor = (priority) => {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
    case 'low':
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
  }
};

const getTypeIcon = (type) => {
  switch (type) {
    case 'bug':
      return '🐞';
    case 'feature':
      return '✨';
    case 'task':
      return '📋';
    default:
      return '📋';
  }
};

const TicketCard = ({ ticket, index, onClick }) => {
  return (
    <Draggable draggableId={String(ticket.id)} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          onClick={() => onClick(ticket)}
          className={`bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm mb-3 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow cursor-pointer ${
            snapshot.isDragging ? 'shadow-lg ring-2 ring-indigo-500 rotate-2' : ''
          }`}
          style={{
            ...provided.draggableProps.style,
          }}
        >
          <div className="flex justify-between items-start mb-2">
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">#{ticket.id}</span>
            <span
              className={`text-xs px-2 py-1 rounded-full font-medium ${getPriorityColor(
                ticket.priority
              )}`}
            >
              {ticket.priority}
            </span>
          </div>
          
          <h3 className="text-gray-900 dark:text-white font-medium mb-2 truncate">{ticket.title}</h3>
          
          <div className="flex justify-between items-center mt-3">
            <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
              <span title={ticket.type} className="text-base">
                {getTypeIcon(ticket.type)}
              </span>
              <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
            </div>
            
            {ticket.assignee && (
              <div 
                className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-xs font-medium text-indigo-700 dark:text-indigo-200"
                title={`Assigned to: ${ticket.assignee.username}`}
              >
                {ticket.assignee.username.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
        </div>
      )}
    </Draggable>
  );
};

export default TicketCard;
