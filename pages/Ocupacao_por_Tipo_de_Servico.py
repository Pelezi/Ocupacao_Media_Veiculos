import streamlit as st
import mysql.connector
import decimal
import pandas as pd

def bd_phoenix(vw_name):
    # Parametros de Login AWS
    config = {
        'user': 'user_automation_jpa',
        'password': 'luck_jpa_2024',
        'host': 'comeia.cixat7j68g0n.us-east-1.rds.amazonaws.com',
        'database': 'test_phoenix_joao_pessoa'
    }
    # Conexão às Views
    conexao = mysql.connector.connect(**config)
    cursor = conexao.cursor()

    request_name = f'SELECT * FROM {vw_name}'

    # Script MySQL para requests
    cursor.execute(request_name)
    # Coloca o request em uma variavel
    resultado = cursor.fetchall()
    # Busca apenas os cabeçalhos do Banco
    cabecalho = [desc[0] for desc in cursor.description]

    # Fecha a conexão
    cursor.close()
    conexao.close()

    # Coloca em um dataframe e converte decimal para float
    df = pd.DataFrame(resultado, columns=cabecalho)
    df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)
    return df

# Configuração da página Streamlit
st.set_page_config(layout='wide')

if not 'df_vehicle_occupation' in st.session_state:
    # Carrega os dados da view `vw_vehicle_ocupation`
    st.session_state.df_vehicle_occupation = bd_phoenix('vw_vehicle_occupation')

st.title('Ocupação por Tipo de Serviço')

st.divider()

# Input de intervalo de data
row0 = st.columns(6)
with row0[0]:
    periodo = st.date_input('Período', value=[], format='DD/MM/YYYY')

# Filtra os dados conforme o intervalo de tempo informado
if len(periodo) == 2:  # Verifica se o intervalo está completo
    data_inicial, data_final = periodo

    df_filtrado = st.session_state.df_vehicle_occupation[
        (st.session_state.df_vehicle_occupation['Data Execucao'] >= data_inicial) &
        (st.session_state.df_vehicle_occupation['Data Execucao'] <= data_final)
    ].reset_index(drop=True)
    
    
    # Conta a quantidade de escalas por veículo, agrupando por Veículo e Escala
    escalas_por_escala = df_filtrado.groupby(['Tipo de Veiculo', 'Veiculo', 'Tipo de Servico'])[['Escala']].nunique().reset_index()
    
    #Renomeia a coluna escala para escalas
    escalas_por_escala.rename(columns={'Escala': 'Escalas'}, inplace=True)
    base_por_escala = df_filtrado.groupby(['Tipo de Veiculo', 'Veiculo', 'Capacidade', 'Escala', 'Tipo de Servico'])[['Total ADT', 'Total CHD']].sum().reset_index()
    
    #Select "Agrupar por:" - Tipo de Serviço ou Tipo de Veículo
    with row0[1]:
        agrupar_por = st.selectbox('Agrupar por:', ['Tipo de Serviço', 'Tipo de Veículo'], index=None)
        
    if agrupar_por == 'Tipo de Serviço':
        # Conta a quantidade de escalas por tipo de serviço, agrupando por Tipo de Serviço
        escalas_por_tipo_servico = df_filtrado.groupby(['Tipo de Servico'])[['Escala']].nunique().reset_index()
        
        #Calcula a porcentagem de escalas por tipo de serviço
        escalas_por_tipo_servico['Porcentagem'] = escalas_por_tipo_servico['Escala'] / escalas_por_tipo_servico['Escala'].sum() * 100
        
        #Renomeia a coluna escala para escalas
        escalas_por_tipo_servico.rename(columns={'Escala': 'Escalas'}, inplace=True)
        
        #Ordena pelo número de escalas
        escalas_por_tipo_servico = escalas_por_tipo_servico.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
        
        #Select Tipo de Serviço
        lista_servicos = escalas_por_tipo_servico['Tipo de Servico'].unique().tolist()
        with row0[2]:
            tipo_servico_selecionado = st.selectbox('Selecionar Tipo de Serviço', sorted(lista_servicos), index=None)
        
        # Se um tipo de serviço for selecionado, exibe a quantidade de escala por veículo e tipo de veículo
        if tipo_servico_selecionado:
            # Filtra o dataframe para o tipo de serviço selecionado
            escalas_base = df_filtrado[df_filtrado['Tipo de Servico'] == tipo_servico_selecionado]
            escalas_por_tipo_veiculo = escalas_base.groupby(['Tipo de Veiculo'])[['Escala']].nunique().reset_index()
            escalas_por_veiculo = escalas_base.groupby(['Tipo de Veiculo', 'Veiculo'])[['Escala']].nunique().reset_index()
            #Calcula a porcentagem de escalas por tipo de veículo e veículo
            escalas_por_tipo_veiculo['Porcentagem'] = escalas_por_tipo_veiculo['Escala'] / escalas_por_tipo_veiculo['Escala'].sum() * 100
            escalas_por_veiculo['Porcentagem'] = escalas_por_veiculo['Escala'] / escalas_por_veiculo['Escala'].sum() * 100
            #Calcula a porcentagem sobre a quantidade total geral de escalas
            escalas_por_tipo_veiculo['Porcentagem Total'] = escalas_por_tipo_veiculo['Escala'] / escalas_por_tipo_servico['Escalas'].sum() * 100
            escalas_por_veiculo['Porcentagem Total'] = escalas_por_veiculo['Escala'] / escalas_por_tipo_servico['Escalas'].sum() * 100
            #Renomeia a coluna escala para escalas
            escalas_por_tipo_veiculo.rename(columns={'Escala': 'Escalas'}, inplace=True)
            escalas_por_veiculo.rename(columns={'Escala': 'Escalas'}, inplace=True)
            #Ordena pelo número de escalas
            escalas_por_tipo_veiculo = escalas_por_tipo_veiculo.sort_values(by='Escalas', ascending=False).reset_index(drop=True)  
            escalas_por_veiculo = escalas_por_veiculo.sort_values(by='Escalas', ascending=False).reset_index(drop=True)          
            
            #Select Tipo de Veículo
            lista_veiculos = escalas_por_tipo_veiculo['Tipo de Veiculo'].unique().tolist()
            with row0[3]:
                tipo_veiculo_selecionado = st.selectbox('Selecionar Tipo de Veículo', sorted(lista_veiculos), index=None)
            
            # Se um tipo de veículo for selecionado, exibe a quantidade de escala por veículo
            if tipo_veiculo_selecionado:
                #Filtra o dataframe para o tipo de veículo selecionado
                escalas_por_veiculo = df_filtrado[
                    (df_filtrado['Tipo de Servico'] == tipo_servico_selecionado) &
                    (df_filtrado['Tipo de Veiculo'] == tipo_veiculo_selecionado)
                ]
                #Conta a quantidade de escalas por veículo
                escalas_por_veiculo = escalas_por_veiculo.groupby(['Veiculo'])[['Escala']].nunique().reset_index()
                #Calcula a porcentagem de escalas por veículo
                escalas_por_veiculo['Porcentagem'] = escalas_por_veiculo['Escala'] / escalas_por_veiculo['Escala'].sum() * 100
                #Calcula a porcentagem sobre a quantidade total geral de escalas
                escalas_por_veiculo['Porcentagem Total'] = escalas_por_veiculo['Escala'] / escalas_por_tipo_servico['Escalas'].sum() * 100
                #Renomeia a coluna escala para escalas
                escalas_por_veiculo.rename(columns={'Escala': 'Escalas'}, inplace=True)
                #Ordena pelo número de escalas
                escalas_por_veiculo = escalas_por_veiculo.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
                
                #Select Veículo
                lista_veiculos = escalas_por_veiculo['Veiculo'].unique().tolist()
                with row0[4]:
                    veiculo_selecionado = st.selectbox('Selecionar Veículo', sorted(lista_veiculos), index=None)
                
                # Se um veículo for selecionado, exibe as escalas associadas
                if veiculo_selecionado:
                    escalas_por_veiculo_selecionado = base_por_escala[(base_por_escala['Tipo de Veiculo'] == tipo_veiculo_selecionado) & (base_por_escala['Veiculo'] == veiculo_selecionado) & (base_por_escala['Tipo de Servico'] == tipo_servico_selecionado)]
                
                    #Select escalas
                    lista_escala = escalas_por_veiculo_selecionado['Escala'].unique().tolist()
                    with row0[5]:
                        escala_selecionada = st.selectbox('Selecionar Escala', sorted(lista_escala), index=None)
                    
                    # Se uma escala for selecionada, exibe os serviços associados
                    if escala_selecionada:
                        escalas_por_servico = df_filtrado[
                            (df_filtrado['Tipo de Veiculo'] == tipo_veiculo_selecionado) &
                            (df_filtrado['Veiculo'] == veiculo_selecionado) &
                            (df_filtrado['Escala'] == escala_selecionada)
                        ]
                        #Remove a coluna tipo de veículo
                        escalas_por_servico = escalas_por_servico.drop(columns=['Tipo de Veiculo'])
                        st.divider()
                        st.subheader(f'Serviços associados a Escala {escala_selecionada}')
                        st.dataframe(escalas_por_servico, hide_index=True, use_container_width=True)
                    st.divider()
                    st.subheader(f'Escalas por Veículo - {tipo_servico_selecionado} - {tipo_veiculo_selecionado} - {veiculo_selecionado}')
                    st.dataframe(escalas_por_veiculo_selecionado, hide_index=True, use_container_width=True)
                st.divider()
                st.subheader(f'Escalas por Tipo de Veículo - {tipo_servico_selecionado} - {tipo_veiculo_selecionado}')
                st.dataframe(escalas_por_veiculo, hide_index=True, use_container_width=True)
            st.divider()
            st.subheader(f'Escalas por Tipo de Veículo - {tipo_servico_selecionado}')
            st.dataframe(escalas_por_tipo_veiculo, hide_index=True, use_container_width=True)
            st.subheader(f'Escalas por Veículo - {tipo_servico_selecionado}')
            st.dataframe(escalas_por_veiculo, hide_index=True, use_container_width=True)
        
        # Exibe o dataframe completo de quantidade de escalas por tipo de serviço
        st.divider()
        st.subheader('Escalas por Tipo de Serviço')
        st.text("Total de Escalas: " + str(escalas_por_tipo_servico['Escalas'].sum()))
        st.dataframe(escalas_por_tipo_servico, hide_index=True, use_container_width=True)
    elif agrupar_por == 'Tipo de Veículo':

        # Conta a quantidade de escalas por tipo de veículo, agrupando por Tipo de Veículo e Tipo de Serviço
        escalas_por_tipo_veiculo = escalas_por_escala.groupby(['Tipo de Veiculo'])[['Escalas']].sum().reset_index()
        escalas_por_tipo_veiculo_tipo_servico = escalas_por_escala.groupby(['Tipo de Veiculo', 'Tipo de Servico'])[['Escalas']].sum().reset_index()
        
        #Calcula a porcentagem de escalas por tipo de veículo
        escalas_por_tipo_veiculo['Porcentagem'] = escalas_por_tipo_veiculo['Escalas'] / escalas_por_tipo_veiculo['Escalas'].sum() * 100
        escalas_por_tipo_veiculo_tipo_servico['Porcentagem'] = escalas_por_tipo_veiculo_tipo_servico['Escalas'] / escalas_por_tipo_veiculo_tipo_servico['Escalas'].sum() * 100
        
        #Ordena pelo número de escalas
        escalas_por_tipo_veiculo = escalas_por_tipo_veiculo.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
        escalas_por_tipo_veiculo_tipo_servico = escalas_por_tipo_veiculo_tipo_servico.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
        
        # Exibe a lista de tipos de veículos para seleção
        lista_veiculos = escalas_por_escala['Tipo de Veiculo'].unique().tolist()
        with row0[2]:
            tipo_veiculo_selecionado = st.selectbox('Selecionar Tipo de Veículo', sorted(lista_veiculos), index=None)

        # Se um tipo de veículo for selecionado, exibe a quantidade de escala por veículo
        if tipo_veiculo_selecionado:
            escalas_por_tipo_veiculo_selecionado = escalas_por_escala[
                escalas_por_escala['Tipo de Veiculo'] == tipo_veiculo_selecionado
            ].reset_index(drop=True)
            escalas_por_tipo_veiculo_selecionado_veiculo = escalas_por_tipo_veiculo_selecionado.groupby(['Veiculo'])[['Escalas']].sum().reset_index()
            escalas_por_tipo_veiculo_selecionado_tipo_servico = escalas_por_tipo_veiculo_selecionado.groupby(['Tipo de Servico'])[['Escalas']].sum().reset_index()
            #Calcula a porcentagem de escalas por tipo de serviço
            escalas_por_tipo_veiculo_selecionado['Porcentagem'] = escalas_por_tipo_veiculo_selecionado['Escalas'] / escalas_por_tipo_veiculo_selecionado['Escalas'].sum() * 100
            escalas_por_tipo_veiculo_selecionado_veiculo['Porcentagem'] = escalas_por_tipo_veiculo_selecionado_veiculo['Escalas'] / escalas_por_tipo_veiculo_selecionado_veiculo['Escalas'].sum() * 100
            escalas_por_tipo_veiculo_selecionado_tipo_servico['Porcentagem'] = escalas_por_tipo_veiculo_selecionado_tipo_servico['Escalas'] / escalas_por_tipo_veiculo_selecionado_tipo_servico['Escalas'].sum() * 100
            #Calcula a porcentagem sobre a quantidade total geral de escalas
            escalas_por_tipo_veiculo_selecionado['Porcentagem Total'] = escalas_por_tipo_veiculo_selecionado['Escalas'] / escalas_por_tipo_veiculo['Escalas'].sum() * 100
            escalas_por_tipo_veiculo_selecionado_veiculo['Porcentagem Total'] = escalas_por_tipo_veiculo_selecionado_veiculo['Escalas'] / escalas_por_tipo_veiculo['Escalas'].sum() * 100
            escalas_por_tipo_veiculo_selecionado_tipo_servico['Porcentagem Total'] = escalas_por_tipo_veiculo_selecionado_tipo_servico['Escalas'] / escalas_por_tipo_veiculo['Escalas'].sum() * 100
            #Ordena pelo número de escalas
            escalas_por_tipo_veiculo_selecionado = escalas_por_tipo_veiculo_selecionado.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
            escalas_por_tipo_veiculo_selecionado_veiculo = escalas_por_tipo_veiculo_selecionado_veiculo.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
            escalas_por_tipo_veiculo_selecionado_tipo_servico = escalas_por_tipo_veiculo_selecionado_tipo_servico.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
            #Remove a coluna Tipo Veículo
            escalas_por_tipo_veiculo_selecionado = escalas_por_tipo_veiculo_selecionado.drop(columns=['Tipo de Veiculo'])
            
            #Select Veículo
            lista_veiculos = escalas_por_tipo_veiculo_selecionado['Veiculo'].unique().tolist()
            with row0[3]:
                veiculo_selecionado = st.selectbox('Selecionar Veículo', sorted(lista_veiculos), index=None)
            
            # Se um veículo for selecionado, exibe a contagem de escalas por tipo de servicço, e a lista das escalas associadas com uma coluna do tipo de serviço
            if veiculo_selecionado:
                escalas_por_veiculo_selecionado = escalas_por_tipo_veiculo_selecionado[escalas_por_tipo_veiculo_selecionado['Veiculo'] == veiculo_selecionado]
                #Calcula a porcentagem de escalas por tipo de serviço
                escalas_por_veiculo_selecionado['Porcentagem'] = escalas_por_veiculo_selecionado['Escalas'] / escalas_por_veiculo_selecionado['Escalas'].sum() * 100
                #Calcula a porcentagem sobre a quantidade total geral de escalas
                escalas_por_veiculo_selecionado['Porcentagem Total'] = escalas_por_veiculo_selecionado['Escalas'] / escalas_por_tipo_veiculo['Escalas'].sum() * 100
                #Ordena pelo número de escalas
                escalas_por_veiculo_selecionado = escalas_por_veiculo_selecionado.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
                
                #Select tipo de serviço
                lista_servicos = escalas_por_veiculo_selecionado['Tipo de Servico'].unique().tolist()
                with row0[4]:
                    tipo_servico_selecionado = st.selectbox('Selecionar Tipo de Serviço', sorted(lista_servicos), index=None)
                
                # Se um tipo de serviço for selecionado, exibe as escalas associadas
                if tipo_servico_selecionado:
                    escalas_por_veiculo_selecionado_tipo_servico_selecionado = base_por_escala[(base_por_escala['Tipo de Veiculo'] == tipo_veiculo_selecionado) & (base_por_escala['Veiculo'] == veiculo_selecionado) & (base_por_escala['Tipo de Servico'] == tipo_servico_selecionado)]
                    
                    #Select escalas
                    lista_escala = escalas_por_veiculo_selecionado_tipo_servico_selecionado['Escala'].unique().tolist()
                    with row0[5]:
                        escala_selecionada = st.selectbox('Selecionar Escala', sorted(lista_escala), index=None)
                        
                    # Se uma escala for selecionada, exibe os serviços associados
                    if escala_selecionada:
                        escalas_por_servico = df_filtrado[
                            (df_filtrado['Tipo de Veiculo'] == tipo_veiculo_selecionado) &
                            (df_filtrado['Veiculo'] == veiculo_selecionado) &
                            (df_filtrado['Tipo de Servico'] == tipo_servico_selecionado) &
                            (df_filtrado['Escala'] == escala_selecionada)
                        ]
                        #Remove a coluna tipo de veículo
                        escalas_por_servico = escalas_por_servico.drop(columns=['Tipo de Veiculo'])
                        st.divider()
                        st.subheader(f'Serviços associados a Escala {escala_selecionada}')
                        st.dataframe(escalas_por_servico, hide_index=True, use_container_width=True)
                        
                    st.divider()
                    st.subheader(f'Escalas por Veículo - {tipo_servico_selecionado} - {tipo_veiculo_selecionado} - {veiculo_selecionado}')
                    st.dataframe(escalas_por_veiculo_selecionado_tipo_servico_selecionado, hide_index=True, use_container_width=True)
                
                st.divider()
                st.subheader(f'Escalas por Veículo e Tipo de Serviço - {tipo_veiculo_selecionado} - {veiculo_selecionado}')
                st.dataframe(escalas_por_veiculo_selecionado, hide_index=True, use_container_width=True)
            
            st.divider()
            st.subheader(f'Escalas por Tipo de Veículo - {tipo_veiculo_selecionado}')
            st.text("Total de Escalas - " + str(tipo_veiculo_selecionado) + ": " + str(escalas_por_tipo_veiculo_selecionado['Escalas'].sum()))
            st.dataframe(escalas_por_tipo_veiculo_selecionado_tipo_servico, hide_index=True, use_container_width=True)
            st.subheader('Escalas por Veículo')
            st.dataframe(escalas_por_tipo_veiculo_selecionado_veiculo, hide_index=True, use_container_width=True)
            st.subheader('Escalas por Veículo e Tipo de Serviço')
            st.dataframe(escalas_por_tipo_veiculo_selecionado, hide_index=True, use_container_width=True)
        # Exibe o dataframe completo de quantidade de escalas por tipo de veículo
        st.divider()
        st.subheader('Escalas por Tipo de Veículo')
        st.text("Total de Escalas: " + str(escalas_por_tipo_veiculo['Escalas'].sum()))
        st.dataframe(escalas_por_tipo_veiculo, hide_index=True, use_container_width=True)
        st.subheader('Escalas por Tipo de Veículo e Tipo de Serviço')
        st.dataframe(escalas_por_tipo_veiculo_tipo_servico, hide_index=True, use_container_width=True)
    else:
        #Agrupa por veículo
        escalas_por_escala_geral = escalas_por_escala.groupby(['Tipo de Veiculo', 'Veiculo'])[['Escalas']].sum().reset_index()
        #Calcula a porcentagem de escalas por veículo
        escalas_por_escala_geral['Porcentagem'] = escalas_por_escala_geral['Escalas'] / escalas_por_escala_geral['Escalas'].sum() * 100
        #Ordena pelo número de escalas
        escalas_por_escala_geral = escalas_por_escala_geral.sort_values(by='Escalas', ascending=False).reset_index(drop=True)
        # Exibe o dataframe completo de quantidade de escalas por veículo ordenado pela quantidade de escalas
        st.divider()
        st.subheader('Escalas por Veículo')
        st.text("Total de Escalas: " + str(escalas_por_escala_geral['Escalas'].sum()))
        st.dataframe(escalas_por_escala_geral, hide_index=True, use_container_width=True)
    