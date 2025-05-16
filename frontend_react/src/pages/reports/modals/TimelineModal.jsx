import React, { useState, useEffect } from 'react';
import { Modal, Spinner } from 'react-bootstrap';
import Timeline from 'react-calendar-timeline';
import "react-calendar-timeline/dist/Timeline.scss";
import moment from 'moment';
import 'moment/locale/es';
import './css/TimelineModal.css';
import { supervisorReportAPI } from '../../../api/supervisorReport.api';

moment.locale('es');

export const TimelineModal = ({ show, onHide, programId, currentDate }) => {
    const [timelineData, setTimelineData] = useState({
        groups: [],
        items: []
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (show && programId) {
            loadTimelineData();
        }
    }, [show, programId]);

    const loadTimelineData = async () => {
        try {
            setLoading(true);
            const response = await supervisorReportAPI.getExecutionTimeline(programId);
            
            console.log('Response del timeline:', response);

            // La respuesta ya viene con el formato correcto {groups: [], items: []}
            setTimelineData({
                groups: response.groups,
                items: response.items.map(item => ({
                    ...item,
                    start_time: moment(item.start_time),
                    end_time: moment(item.end_time)
                }))
            });

        } catch (error) {
            console.error('Error cargando timeline:', error);
            setError('Error al cargar los datos del timeline');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal 
            show={show} 
            onHide={onHide} 
            size="xl" 
            className="timeline-modal"
            dialogClassName="modal-90w"
        >
            <Modal.Header closeButton>
                <Modal.Title>Timeline de Producción</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <div className="timeline-container">
                    {loading ? (
                        <div className="text-center p-4">
                            <Spinner animation="border" />
                        </div>
                    ) : error ? (
                        <div className="text-center p-4 text-danger">
                            {error}
                        </div>
                    ) : timelineData.groups.length > 0 ? (
                        <Timeline
                            groups={timelineData.groups}
                            items={timelineData.items}
                            defaultTimeStart={moment(currentDate).startOf('day')}
                            defaultTimeEnd={moment(currentDate).add(1, 'day')}
                            sidebarWidth={250}
                            lineHeight={50}
                            itemHeightRatio={0.8}
                            canMove={false}
                            canResize={false}
                            stackItems
                            traditionalZoom
                            showCursorLine
                            itemRenderer={({ item, itemContext, getItemProps }) => {
                                const { left: leftResizer, right: rightResizer } = itemContext.dimensions;
                                return (
                                    <div
                                        {...getItemProps({
                                            className: `timeline-custom-item estado-${item.estado}`,
                                            style: {
                                                left: leftResizer,
                                                width: rightResizer - leftResizer,
                                                position: 'absolute',
                                                height: '100%'
                                            }
                                        })}
                                        title={item.itemProps['data-tooltip']}
                                    >
                                        <div className="timeline-item-content">
                                            {item.title}
                                        </div>
                                    </div>
                                );
                            }}
                        />
                    ) : (
                        <div className="text-center p-4">
                            No hay tareas para mostrar en el timeline
                        </div>
                    )}
                </div>
            </Modal.Body>
        </Modal>
    );
};