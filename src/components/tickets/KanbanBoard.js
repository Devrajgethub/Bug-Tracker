import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import TicketCard from './TicketCard';
import { ticketService } from '../../services/ticketService';

const columns = {
  todo: { title: 'To Do', id: 'todo' },
  in_progress: { title: 'In Progress', id: 'in_progress' },
  in_review: { title: 'In Review', id: 'in_review' },
  done: { title: 'Done', id: 'done' },
};

const KanbanBoard = ({ tickets, onTicketUpdated, onTicketClick }) => {
  const [boardData, setBoardData] = useState({
    todo: [],
    in_progress: [],
    in_review: [],
    done: [],
  });

  useEffect(() => {
    // Group tickets by status
    const grouped = {
      todo: [],
      in_progress: [],
      in_review: [],
      done: [],
    };

    tickets.forEach((ticket) => {
      if (grouped[ticket.status]) {
        grouped[ticket.status].push(ticket);
      }
    });

    setBoardData(grouped);
  }, [tickets]);

  const onDragEnd = async (result) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;

    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return;
    }

    const startColumn = source.droppableId;
    const finishColumn = destination.droppableId;

    // Optimistic update
    const startList = Array.from(boardData[startColumn]);
    const finishList = Array.from(boardData[finishColumn]);
    const ticket = startList.find(t => String(t.id) === draggableId);
    
    // Remove from start
    startList.splice(source.index, 1);

    if (startColumn === finishColumn) {
      startList.splice(destination.index, 0, ticket);
      setBoardData({
        ...boardData,
        [startColumn]: startList,
      });
    } else {
      // Add to finish
      // Update ticket status locally
      const updatedTicket = { ...ticket, status: finishColumn };
      finishList.splice(destination.index, 0, updatedTicket);
      
      setBoardData({
        ...boardData,
        [startColumn]: startList,
        [finishColumn]: finishList,
      });

      // API Call
      try {
        await ticketService.updateTicket(ticket.id, { status: finishColumn });
        if (onTicketUpdated) onTicketUpdated();
      } catch (error) {
        console.error("Failed to update ticket status", error);
        // Revert (could be implemented by reloading or undoing state)
      }
    }
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="flex h-full overflow-x-auto pb-4 space-x-4">
        {Object.values(columns).map((column) => (
          <div
            key={column.id}
            className="flex-shrink-0 w-80 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
          >
            <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-4 flex justify-between items-center">
              {column.title}
              <span className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs px-2 py-1 rounded-full">
                {boardData[column.id].length}
              </span>
            </h3>
            <Droppable droppableId={column.id}>
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`min-h-[200px] transition-colors rounded-lg ${
                    snapshot.isDraggingOver ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                  }`}
                >
                  {boardData[column.id].map((ticket, index) => (
                    <TicketCard 
                      key={ticket.id} 
                      ticket={ticket} 
                      index={index} 
                      onClick={onTicketClick}
                    />
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </div>
        ))}
      </div>
    </DragDropContext>
  );
};

export default KanbanBoard;
